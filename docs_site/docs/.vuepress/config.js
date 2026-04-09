import { defineUserConfig } from 'vuepress'
import { defaultTheme } from '@vuepress/theme-default'
import { viteBundler } from '@vuepress/bundler-vite'
import { markdownChartPlugin } from '@vuepress/plugin-markdown-chart'

export default defineUserConfig({
  bundler: viteBundler(),
  base: '/',
  title: 'HyperFlow',
  description: 'Self-improving agent framework powered by LangChain and LangGraph.',
  head: [
    ['link', { rel: 'icon', type: 'image/png', href: '/logo.png' }],
    ['meta', { name: 'theme-color', content: '#3eaf7c' }],
    ['meta', { name: 'apple-mobile-web-app-capable', content: 'yes' }],
    ['meta', { name: 'apple-mobile-web-app-status-bar-style', content: 'black' }],
    ['meta', { name: 'author', content: 'lablnet' }],
    ['meta', { name: 'keywords', content: 'AI, Generative AI, LangChain, LangGraph, Quality Diversity, Evolution, LLM, Agents' }]
  ],
  plugins: [
    markdownChartPlugin({
      mermaid: true,
    }),
  ],
  theme: defaultTheme({
    logo: '/logo.png',
    repo: 'lablnet/HyperFlow',
    docsDir: 'docs_site/docs',
    navbar: [
      { text: 'Home', link: '/' },
      { text: 'Guide', link: '/guide/basic-concepts.md' },
      { text: 'Examples', link: '/guide/examples.md' },
    ],
    sidebar: {
      '/guide/': [
        {
          text: 'Guide',
          children: [
            '/guide/installation.md',
            '/guide/basic-concepts.md',
            '/guide/advanced-concepts.md',
            '/guide/limitations.md',
            '/guide/examples.md',
            '/guide/contributing.md',
            '/guide/citation.md',
          ],
        },
      ],
    },
  }),
})
