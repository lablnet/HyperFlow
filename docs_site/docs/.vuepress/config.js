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
    ['link', { rel: 'icon', href: '/favicon.ico' }],
  ],
  plugins: [
    markdownChartPlugin({
      mermaid: true,
    }),
  ],
  theme: defaultTheme({
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
            '/guide/examples.md',
            '/guide/contributing.md',
          ],
        },
      ],
    },
  }),
})
