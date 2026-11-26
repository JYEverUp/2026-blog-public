import Link from 'next/link'
import { ChevronDown, ChevronRight } from 'lucide-react'
import type { BlogIndexItem } from '../types'
import archive from '../archive-series.json'

const chapterSlugs = new Set(archive.topics.flatMap(topic => topic.series.flatMap(series => series.chapters)))
const chapterTitles: Record<string, string> = archive.chapterTitles

export function isArchiveChapter(item: BlogIndexItem) {
	return chapterSlugs.has(item.slug)
}

function getChapterTitle(item: BlogIndexItem) {
	const title = item.title?.replace(/^(?:第\s*\d+\s*[章节][：:\s]*|\d{1,3}(?:[、．]|\.(?!\d))\s*)/u, '')
	return chapterTitles[item.slug] ?? (title || item.slug)
}

export function ArchiveChapters({ items, isRead }: { items: BlogIndexItem[]; isRead: (slug: string) => boolean }) {
	const itemsBySlug = new Map(items.map(item => [item.slug, item]))

	return (
		<div className='space-y-2'>
			{archive.topics.map(topic => {
				const series = topic.series
					.map(series => ({
						title: series.title,
						chapters: series.chapters.flatMap(slug => {
							const item = itemsBySlug.get(slug)
							return item ? [item] : []
						})
					}))
					.filter(series => series.chapters.length > 0)
				const count = series.reduce((total, series) => total + series.chapters.length, 0)
				if (!count) return null

				return (
					<details key={topic.title} className='group/topic overflow-hidden rounded-xl border border-current/10 bg-white/20'>
						<summary className='hover:text-brand focus-visible:ring-brand flex min-h-11 cursor-pointer list-none items-center gap-3 px-3 py-2 text-sm font-medium transition-colors focus-visible:ring-2 focus-visible:ring-inset [&::-webkit-details-marker]:hidden'>
							<span className='flex-1'>{topic.title}</span>
							<span className='text-secondary shrink-0 text-xs font-normal tabular-nums'>{count} 篇</span>
							<ChevronDown
								aria-hidden='true'
								className='text-secondary h-4 w-4 shrink-0 transition-transform group-open/topic:rotate-180 motion-reduce:transition-none'
							/>
						</summary>
						<div className='space-y-4 border-t border-current/10 px-3 pt-2 pb-3 sm:px-4'>
							{series.map(series => (
								<section key={series.title} aria-label={series.title}>
									{series.title !== topic.title && <h3 className='text-secondary px-2 pt-1 pb-1.5 text-xs font-medium'>{series.title}</h3>}
									<ol className='divide-y divide-current/10'>
										{series.chapters.map(item => (
											<li key={item.slug}>
												<Link
													href={`/blog/${item.slug}`}
													prefetch={false}
													className='group/chapter hover:text-brand focus-visible:ring-brand flex min-h-10 items-center gap-3 rounded-md px-2 py-2 text-sm transition-colors focus-visible:ring-2 focus-visible:ring-inset'>
													<span className='min-w-0 flex-1 break-words'>{getChapterTitle(item)}</span>
													{isRead(item.slug) && <span className='text-secondary shrink-0 text-xs'>已阅读</span>}
													<ChevronRight aria-hidden='true' className='text-secondary group-hover/chapter:text-brand h-3.5 w-3.5 shrink-0' />
												</Link>
											</li>
										))}
									</ol>
								</section>
							))}
						</div>
					</details>
				)
			})}
		</div>
	)
}
