import MarkdownIt from 'markdown-it'
import markdownLink from 'markdown-it-link-attributes'
import hljs from 'highlight.js'


const md = new MarkdownIt({
  linkify: true,
  breaks: true,
  highlight: (str, lang) => {
    let content = str
    if (lang && hljs.getLanguage(lang)) {
      try {
        content = hljs.highlight(str, {
          language: lang,
          ignoreIllegals: true
        }).value
      } catch (e) {
        console.log('Syntax highlighting error', e)
        return str
      }
    } else {
      content = md.utils.escapeHtml(str)
    }

    lang = (lang || 'txt')
    // return [
    //   '<pre class="code-prefix"><div>',
    //   `<div class="code-blck-header">${lang}<div class="copy-button"><button class="copy-action"><svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" style="padding-top: 1px; margin-bottom: -1px; margin-right: 4px;" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>Copy code</button></div>`,
    //   '</div><div class="code-body overflow-y-auto">',
    //   `<pre><code class="language-${lang}">${content}</code></pre>`,
    //   '</div></div></pre>'
    // ].join('')
    return [
      '<pre class="code-prefix"><div>',
      `<div class="code-blck-header">${lang}`,
      '</div><div class="code-body overflow-y-auto">',
      `<pre><code class="language-${lang}">${content}</code></pre>`,
      '</div></div></pre>'
    ].join('')
  }
})

md.use(markdownLink, { attrs: { target: '_blank', rel: 'noopener' } })

export const renderMarkDown = (content) => {
  return md.render(content)
}
