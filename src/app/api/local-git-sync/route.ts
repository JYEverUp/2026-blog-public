import { GITHUB_CONFIG } from '@/consts'
import { pullLocalGit } from '@/lib/local-git-sync'

export const runtime = 'nodejs'

let pendingSync: Promise<boolean> | undefined

export async function POST(request: Request) {
	if (process.env.NODE_ENV !== 'development' || process.env.NEXT_PUBLIC_BLOG_LOCAL_GIT_SYNC !== '1') {
		return new Response(null, { status: 404 })
	}

	const host = request.headers.get('host')
	if (!host || !/^(?:localhost|127\.0\.0\.1)(?::\d+)?$/.test(host) || request.headers.get('origin') !== 'http://' + host) {
		return new Response(null, { status: 403 })
	}

	const { OWNER, REPO, BRANCH } = GITHUB_CONFIG
	try {
		pendingSync ??= pullLocalGit(process.cwd(), 'https://github.com/' + OWNER + '/' + REPO + '.git', BRANCH).finally(() => {
			pendingSync = undefined
		})
		return Response.json({ updated: await pendingSync })
	} catch (error) {
		const message = error instanceof Error && !('code' in error) ? error.message : '无法读取本地 Git 工作目录。'
		return Response.json({ message }, { status: 409 })
	}
}
