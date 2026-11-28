$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$siteUrl = 'http://127.0.0.1:2025'
$logDirectory = Join-Path $env:LOCALAPPDATA '2025-blog'

function Test-BlogReady {
    try {
        $response = Invoke-WebRequest -Uri $siteUrl -UseBasicParsing -TimeoutSec 3
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

try {
    if (-not (Test-BlogReady)) {
        $listener = Get-NetTCPConnection -LocalPort 2025 -State Listen -ErrorAction SilentlyContinue
        if (-not $listener) {
            $node = (Get-Command node.exe -ErrorAction Stop).Source
            $next = Join-Path $projectRoot 'node_modules\next\dist\bin\next'
            if (-not (Test-Path -LiteralPath $next)) {
                throw 'Dependencies are missing. Run pnpm install in the project folder.'
            }
            New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
            $server = Start-Process -FilePath $node -ArgumentList @(
                ('"{0}"' -f $next), 'dev', '--turbopack', '-p', '2025', '--hostname', '127.0.0.1'
            ) -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru `
                -RedirectStandardOutput (Join-Path $logDirectory 'server.log') `
                -RedirectStandardError (Join-Path $logDirectory 'server-error.log')
        }
        $deadline = (Get-Date).AddMinutes(3)
        while (-not (Test-BlogReady)) {
            if ($server -and $server.HasExited) {
                throw "Server exited. See logs in $logDirectory"
            }
            if ((Get-Date) -gt $deadline) {
                throw "Startup timed out. See logs in $logDirectory"
            }
            Start-Sleep -Seconds 1
        }
    }
    Start-Process $siteUrl
} catch {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, '2025 Blog') | Out-Null
    exit 1
}
