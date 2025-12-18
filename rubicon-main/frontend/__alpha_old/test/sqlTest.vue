<template>
  <v-container fluid class="px-0 mt-0 pt-4" :style="{ background: $vuetify.theme.themes.light.background }">
    <v-row class="px-8 pt-2 pb-0 my-0 mx-0 d-flex justify-end">
      <v-btn @click="saveToRedis" small class="mr-2 info">
        LOAD FROM SQL REPOSITORY
      </v-btn>
      <v-btn @click="saveToRedis" small class="mr-2 info">
        SAVE TO SQL REPOSITORY
      </v-btn>
    </v-row>
    <div class="px-8 mx-0"  style="font-weight: 800;">SQL</div>
    <v-row class="px-8 py-4 mx-0" style="min-height: 560px;">
      <codemirror v-model="sql" :options="cmOptions">
      </codemirror>
    </v-row>
    <v-row class="px-8 py-2 my-0 mx-0 d-flex justify-end">

      <v-btn @click="executeCode" small class="primary">
        RUN
      </v-btn>
    </v-row>
    <div class="px-8"  style="font-weight: 800;">Execution Result</div>
    <v-row class="px-8 py-4 mx-0" style="min-height: 200px;">
      <codemirror v-model="result" :options="cmOptionsResult">
      </codemirror>
    </v-row>
  </v-container>
</template>

<script>
import { codemirror } from 'vue-codemirror'
import 'codemirror/lib/codemirror.css'

import 'codemirror/mode/sql/sql.js'
import 'codemirror/theme/vscode-dark.css'

import 'codemirror/addon/selection/active-line.js'

// styleSelectedText
import 'codemirror/addon/selection/mark-selection.js'

// hint
import 'codemirror/addon/hint/show-hint.js'
import 'codemirror/addon/hint/show-hint.css'

// highlightSelectionMatches
import 'codemirror/addon/scroll/annotatescrollbar.js'
import 'codemirror/addon/search/matchesonscrollbar.js'
import 'codemirror/addon/search/match-highlighter.js'

// keyMap
import 'codemirror/mode/clike/clike.js'
import 'codemirror/addon/edit/matchbrackets.js'
import 'codemirror/addon/comment/comment.js'
import 'codemirror/addon/dialog/dialog.js'
import 'codemirror/addon/dialog/dialog.css'
import 'codemirror/addon/search/searchcursor.js'
import 'codemirror/addon/search/search.js'
import 'codemirror/keymap/sublime.js'

// foldGutter
import 'codemirror/addon/fold/foldgutter.css'
import 'codemirror/addon/fold/brace-fold.js'
import 'codemirror/addon/fold/comment-fold.js'
import 'codemirror/addon/fold/foldcode.js'
import 'codemirror/addon/fold/foldgutter.js'
import 'codemirror/addon/fold/indent-fold.js'
import 'codemirror/addon/fold/markdown-fold.js'
import 'codemirror/addon/fold/xml-fold.js'
// import { PrismEditor } from 'vue-prism-editor'
// import { highlight, languages } from 'prismjs/components/prism-core'
// import 'prismjs/components/prism-clike'
// import 'prismjs/components/prism-python'
// import '@/assets/styles/prism-vsc-dark-plus.css'

export default {
  components: {
    // PrismEditor
    codemirror
  },
  data: () => ({
    sql: 'SELECT "year" as "년", week as "주", product as "제품", SUM(sales_performance) AS "판매량", SUM(predict_sales_performance) AS "예상 판매량"\nFROM public.alpha_example_sales\nWHERE year = 2023 AND week in (23, 24, 25) AND product in (\'S23\',\'S23 Ultra\') AND org = \'C100\'\nGROUP BY "year", week, product\nORDER BY "year", week, product;',
    result: null,
    cmOptions: {
      tabSize: 4,
      styleActiveLine: true,
      lineNumbers: true,
      line: true,
      foldGutter: true,
      styleSelectedText: true,
      mode: 'text/x-pgsql',
      theme: 'vscode-dark',
      // theme: 'lesser-dark',
      keyMap: 'sublime',
      matchBrackets: true,
      showCursorWhenSelecting: true,
      extraKeys: { Ctrl: 'autocomplete' },
      gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter'],
      hintOptions: {
        completeSingle: false
      }
    },
    cmOptionsResult: {
      tabSize: 4,
      styleActiveLine: true,
      lineNumbers: true,
      line: true,
      foldGutter: true,
      styleSelectedText: true,
      mode: {
        name: 'javascript',
        json: true,
        statementIndent: 2
      },
      theme: 'vscode-dark',
      keyMap: 'sublime',
      matchBrackets: true,
      showCursorWhenSelecting: true,
      extraKeys: { Ctrl: 'autocomplete' },
      gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter'],
      hintOptions: {
        completeSingle: false
      }
    }
    // cmOptions: {
    //   // codemirror options
    //   tabSize: 4,

    //   lineNumbers: true,
    //   line: true
    //   // more codemirror options, 更多 codemirror 的高级配置...
    // }
  }),
  methods: {
    // highlighter (code) {
    //   return highlight(code, languages.python)
    // },
    executeCode () {
      // console.log(this.code)
      this.result = null
      this.$alphaTest.sql.run(this.sql).then(response => {
        let responseText = ''
        const responseArray = String(response.data).split(/\r?\n/)
        for (var i = 0; i < responseArray.length; i++) {
          // console.log(responseArray[i])
          try {
            responseText = responseText + JSON.stringify(JSON.parse(responseArray[i]), null, 2) + '\n'
          } catch (error) {
            if (responseArray[i] !== '') {
              responseText = responseText + responseArray[i] + '\n'
            }
          }
        }
        // console.log(responseText)
        this.result = responseText
      })
    },
    saveToRedis () {
      // console.log(this.code)
      this.result = null
      this.$alphaTest.code.saveToRedis(this.code).then(response => {
        this.result = response.data
      })
    }
  }
  // mounted () {
  //   console.log(this.$refs.code)
  // }
}
</script>

<style lang="css">
.vue-codemirror {
  width: 100%;
}

.CodeMirror {
  border-radius:4px 4px 4px 4px !important;
  height: 100%;
}
</style>
