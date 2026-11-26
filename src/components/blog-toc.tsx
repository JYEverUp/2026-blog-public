'use client'

import clsx from 'clsx'
import { motion } from 'motion/react'
import { useEffect, useMemo, useState } from 'react'

type TocItem = {
	id: string
	text: string
	level: number
}

type BlogTocProps = {
	toc: TocItem[]
	delay?: number
}

export function BlogToc({ toc, delay = 0 }: BlogTocProps) {
	const [activeIds, setActiveIds] = useState<Set<string>>(new Set())
	const baseLevel = toc.reduce((level, item) => Math.min(level, item.level), 6)
	const minActiveId = useMemo(() => {
		return Array.from(activeIds).sort((a, b) => toc.findIndex(item => item.id === a) - toc.findIndex(item => item.id === b))[0]
	}, [activeIds, toc])

	useEffect(() => {
		if (toc.length === 0) return

		const observers = new Map<string, IntersectionObserver>()

		// Create observers for each heading
		toc.forEach(item => {
			const element = document.getElementById(item.id)
			if (!element) return

			const observer = new IntersectionObserver(
				entries => {
					entries.forEach(entry => {
						setActiveIds(prev => {
							const newSet = new Set(prev)
							if (entry.isIntersecting) newSet.add(entry.target.id)
							else newSet.delete(entry.target.id)

							return newSet
						})
					})
				},
				{
					rootMargin: '-100px 0px -100px 0px',
					threshold: 0
				}
			)

			observer.observe(element)
			observers.set(item.id, observer)
		})

		return () => {
			observers.forEach(observer => observer.disconnect())
		}
	}, [toc])

	return (
		<motion.div
			initial={{ opacity: 0, scale: 0.8 }}
			animate={{ opacity: 1, scale: 1 }}
			transition={{ delay }}
			className='bg-card w-full rounded-xl border p-3 text-sm'>
			<h2 className='text-secondary mb-2 font-medium'>目录</h2>
			<div className='relative max-h-[300px] space-y-2 overflow-auto'>
				{toc.length === 0 && <div className='text-secondary'>暂无</div>}
				{toc.map(item => (
					<a
						key={item.id + item.level}
						href={`#${encodeURIComponent(item.id)}`}
						className={clsx('hover:text-brand relative block [overflow-wrap:anywhere] transition-colors', item.id === minActiveId && 'text-brand')}
						style={{ paddingInlineStart: (item.level - baseLevel) * 8 }}>
						{item.text}
					</a>
				))}
			</div>
		</motion.div>
	)
}
