import { execFile } from 'node:child_process'
import { relative } from 'node:path'
import { promisify } from 'node:util'

const execFileAsync = promisify(execFile)

export async function pullLocalGit(cwd: string, expectedRemote: string, branch: string): Promise<boolean> {
	const runGit = async (args: string[], timeout?: number) => {
		const { stdout } = await execFileAsync('git', args, {
			cwd,
			timeout,
			windowsHide: true,
			env: { ...process.env, GIT_TERMINAL_PROMPT: '0' }
		})
		return stdout.trim()
	}

	const root = await runGit(['rev-parse', '--show-toplevel'])
	const activeBranch = await runGit(['symbolic-ref', '--quiet', '--short', 'HEAD'])
	const remote = await runGit(['remote', 'get-url', 'origin'])
	if (relative(root, cwd) || activeBranch !== branch || remote.toLowerCase() !== expectedRemote.toLowerCase()) {
		throw new Error('本地仓库或分支与博客的 GitHub 配置不一致。')
	}

	const trackingRef = 'refs/remotes/origin/' + branch
	const before = await runGit(['rev-parse', 'HEAD'])
	try {
		await runGit(['fetch', '--no-tags', 'origin', 'refs/heads/' + branch + ':' + trackingRef], 30000)
	} catch {
		throw new Error('拉取 GitHub 失败，请检查网络后重试。')
	}

	try {
		await runGit(['merge', '--ff-only', '--no-autostash', '--no-overwrite-ignore', trackingRef])
	} catch {
		throw new Error('存在本地改动或分支冲突，Git 已停止同步。')
	}

	return (await runGit(['rev-parse', 'HEAD'])) !== before
}
