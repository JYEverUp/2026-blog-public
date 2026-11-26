import { Marked, Renderer } from 'marked'
import type { Tokens } from 'marked'
import { htmlToDOM, type DOMNode } from 'html-react-parser'

export type TocItem = { id: string; text: string; level: number }

export interface MarkdownRenderResult {
	html: string
	toc: TocItem[]
}

export function slugify(text: string): string {
	return text
		.toLowerCase()
		.replace(/[^a-z0-9\u4e00-\u9fa5\s-]/g, '')
		.trim()
		.replace(/\s+/g, '-')
}

function getHeadingText(nodes: DOMNode[]): string {
	return nodes.map(node => {
		if (node.type === 'text') return node.data
		if (node.type !== 'tag') return ''
		if (node.name === 'img') return node.attribs.alt || ''
		if (node.name === 'br') return ' '
		return getHeadingText(node.children as DOMNode[])
	}).join('')
}

// Lazy load shiki to handle environments where it's not available (e.g., Cloudflare Workers)
let shikiModule: typeof import('shiki') | null = null
let shikiLoadAttempted = false

async function loadShiki() {
	if (shikiLoadAttempted) {
		return shikiModule
	}
	shikiLoadAttempted = true

	try {
		shikiModule = await import('shiki')
		return shikiModule
	} catch (error) {
		console.warn('Failed to load shiki module:', error)
		return null
	}
}

// Lazy load katex to handle environments where it's not available (e.g., Cloudflare Workers)
let katexModule: typeof import('katex') | null = null
let katexLoadAttempted = false

async function loadKatex() {
	if (katexModule) return katexModule
	if (katexLoadAttempted) return null
	katexLoadAttempted = true

	try {
		// katex is published as CJS; depending on bundler/runtime the dynamic import
		// may return either the exports object directly or as `default`.
		const mod: any = await import('katex')
		katexModule = (mod?.default ?? mod) as any
		return katexModule
	} catch (error) {
		console.warn('Failed to load katex module:', error)
		return null
	}
}

export async function renderMarkdown(markdown: string): Promise<MarkdownRenderResult> {
	// Load optional renderers first so they apply on the FIRST lex/parse pass.
	// (If we lex before registering extensions, math tokens won't ever be produced on a cold refresh.)
	const marked = new Marked()
	const highlightedCode = new Map<Tokens.Code, string>()
	const toc: TocItem[] = []
	const usedIds = new Set<string>()
	const reservedIds = new Set<string>()
	const [shiki, katex] = await Promise.all([loadShiki(), loadKatex()])

	// Render HTML with heading ids
	const renderer = new Renderer()

	renderer.heading = function (token: Tokens.Heading) {
		const html = this.parser.parseInline(token.tokens)
		const text = getHeadingText(htmlToDOM(html)).replace(/\s+/g, ' ').trim()
		// Keep the original fragment for the first heading with each slug.
		const baseId = slugify(token.text) || 'section'
		let id = baseId
		let suffix = 1
		while (usedIds.has(id) || (id !== baseId && reservedIds.has(id))) {
			id = `${baseId}-${++suffix}`
		}
		usedIds.add(id)
		if (text) toc.push({ id, text, level: token.depth })
		return `<h${token.depth} id="${id}">${html}</h${token.depth}>`
	}

	renderer.code = (token: Tokens.Code) => {
		const escapedCode = token.text.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
		const html = highlightedCode.get(token) ?? `<pre><code>${escapedCode}</code></pre>`
		return `<pre data-code="${escapedCode}">${html}</pre>`
	}

	renderer.listitem = (token: Tokens.ListItem) => {
		// Render inline markdown inside list items (e.g. links, emphasis)
		let inner = token.text
		let tokens = token.tokens

		if (token.task) tokens = tokens.slice(1)
		inner = marked.parser(tokens) as string

		if (token.task) {
			const checkbox = token.checked ? '<input type="checkbox" checked disabled />' : '<input type="checkbox" disabled />'
			return `<li class="task-list-item">${checkbox} ${inner}</li>\n`
		}

		return `<li>${inner}</li>\n`
	}

	const renderMath = (content: string, displayMode: boolean) => {
		if (!katex) {
			// Keep original delimiters if katex is not available
			return displayMode ? `$$${content}$$` : `$${content}$`
		}

		try {
			return katex.renderToString(content, {
				displayMode,
				throwOnError: false,
				output: 'html',
				strict: 'ignore'
			})
		} catch {
			return displayMode ? `$$${content}$$` : `$${content}$`
		}
	}

	// Register extensions BEFORE lexing so math gets tokenized on cold refresh.
	marked.use({
		renderer,
		extensions: [
			// Block math: $$ ... $$
			{
				name: 'mathBlock',
				level: 'block',
				start(src: string) {
					return src.indexOf('$$')
				},
				tokenizer(src: string) {
					const match = src.match(/^\$\$([\s\S]+?)\$\$(?:\n+|$)/)
					if (!match) return
					return {
						type: 'mathBlock',
						raw: match[0],
						text: match[1].trim()
					} as any
				},
				renderer(token: any) {
					return `${renderMath(token.text || '', true)}\n`
				}
			},
			// Inline math: $ ... $
			{
				name: 'mathInline',
				level: 'inline',
				start(src: string) {
					const idx = src.indexOf('$')
					return idx === -1 ? undefined : idx
				},
				tokenizer(src: string) {
					// Avoid $$ (block) and escaped dollars
					if (src.startsWith('$$')) return
					if (src.startsWith('\\$')) return

					const match = src.match(/^\$([^\n$]+?)\$/)
					if (!match) return

					const inner = match[1]
					// Heuristic: require some non-space content
					if (!inner || !inner.trim()) return

					return {
						type: 'mathInline',
						raw: match[0],
						text: inner.trim()
					} as any
				},
				renderer(token: any) {
					return renderMath(token.text || '', false)
				}
			}
		]
	})

	// Pre-process with marked lexer first (after extensions are registered)
	const tokens = marked.lexer(markdown)

	marked.walkTokens(tokens, token => {
		if (token.type === 'heading') reservedIds.add(slugify((token as Tokens.Heading).text) || 'section')
	})

	if (shiki) {
		const codeBlocks: Tokens.Code[] = []
		marked.walkTokens(tokens, token => {
			if (token.type === 'code') codeBlocks.push(token as Tokens.Code)
		})
		for (const token of codeBlocks) {
			try {
				const html = await shiki.codeToHtml(token.text, {
					lang: token.lang?.toLowerCase() || 'text',
					theme: 'one-light'
				})
				highlightedCode.set(token, html)
			} catch {
				// Render the escaped code when its language is unavailable.
			}
		}
	}
	const html = (marked.parser(tokens) as string) || ''

	return { html, toc }
}
