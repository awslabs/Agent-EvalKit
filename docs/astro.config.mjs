// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// GitHub Pages serves this project site under /<repo>/. The deploy workflow passes ASTRO_SITE and
// ASTRO_BASE, and the defaults below match awslabs/Agent-EvalKit for local builds.
const site = process.env.ASTRO_SITE ?? 'https://awslabs.github.io';
const base = process.env.ASTRO_BASE ?? '/Agent-EvalKit/';

export default defineConfig({
	site,
	base,
	integrations: [
		starlight({
			title: 'Agent-EvalKit',
			description: 'AI assistant that automates evaluation processes for your AI agents.',
			customCss: ['./src/styles/custom.css'],
			expressiveCode: {
				// Neutral GitHub themes to match the site, in titled window frames.
				themes: ['github-light-default', 'github-dark-default'],
				useStarlightDarkModeSwitch: true,
				useStarlightUiThemeColors: false,
				defaultProps: { wrap: true, preserveIndent: true },
				styleOverrides: {
					borderRadius: '14px',
					borderWidth: '1px',
					borderColor: 'var(--sl-color-hairline-shade)',
					codeFontFamily: 'var(--sl-font-system-mono)',
					codeFontSize: '0.8125rem',
					codeLineHeight: '1.7',
					codePaddingBlock: '1.1rem',
					codePaddingInline: '1.25rem',
					uiFontFamily: 'var(--sl-font)',
					uiFontSize: '0.8125rem',
					frames: {
						shadowColor: 'rgb(0 0 0 / 0.06)',
						frameBoxShadowCssValue: '0 1px 2px rgb(0 0 0 / 0.04), 0 8px 24px rgb(0 0 0 / 0.06)',
						editorTabBarBorderBottomColor: 'var(--sl-color-hairline-shade)',
						terminalTitlebarBorderBottomColor: 'var(--sl-color-hairline-shade)',
						terminalTitlebarDotsOpacity: '0.35',
						inlineButtonBorder: 'var(--sl-color-hairline-shade)',
						tooltipSuccessBackground: '#0d0d0d',
					},
					textMarkers: {
						markBackground: 'rgb(42 120 214 / 0.10)',
						markBorderColor: '#2a78d6',
					},
				},
			},
			components: {
				// Blog posts get an article header with dateline, standfirst, authors, and cover art.
				PageTitle: './src/components/PageTitle.astro',
				// Text links for Docs, Examples, and Blog sit before the GitHub icon in the header.
				SocialIcons: './src/components/SocialIcons.astro',
			},
			social: [
				{ icon: 'github', label: 'GitHub', href: 'https://github.com/awslabs/Agent-EvalKit' },
			],
			sidebar: [
				{ label: 'Overview', slug: 'guides/overview' },
				{
					label: 'Getting Started',
					items: [
						{ label: 'Installation', slug: 'guides/installation' },
						{ label: 'Quick start', slug: 'guides/quick-start' },
						{ label: 'Command reference', slug: 'guides/commands' },
					],
				},
				{
					label: 'Examples',
					items: [{ label: 'QA agent evaluation', slug: 'examples/qa-agent-evaluation' }],
				},
				{
					label: 'Blog',
					items: [
						{ label: 'Overview', slug: 'blog' },
						{ label: 'How we train small judges for agent traces', slug: 'blog/train-your-own-judge' },
					],
				},
			],
		}),
	],
});
