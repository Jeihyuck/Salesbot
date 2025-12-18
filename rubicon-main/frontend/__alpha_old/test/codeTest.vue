<template>
  <v-container fluid class="px-0 mt-0 pt-4" :style="{ background: $vuetify.theme.themes.light.background }">
    <v-row class="px-8 pt-2 pb-0 my-0 mx-0 d-flex justify-end">
      <v-btn @click="saveToRedis" small class="mr-2 info">
        LOAD FROM CODE REPOSITORY
      </v-btn>
      <v-btn @click="saveToRedis" small class="mr-2 info">
        SAVE TO CODE REPOSITORY
      </v-btn>
    </v-row>
    <div class="px-8 mx-0"  style="font-weight: 800;">Python Code</div>
    <v-row class="px-8 py-4 mx-0" style="min-height: 560px;">
      <codemirror v-model="code" :options="cmOptions">
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

export default {
  components: {
    // PrismEditor
    codemirror
  },
  data: () => ({
    code: 'def test(a):\n  c = plus(a, 3)\n  print(\'result\')\n  print(c)\n  \ntest(4)\n\nfrom apps.alpha_auth.models import Alpha_User\nprint(list(Alpha_User.objects.values()))\n',
    // code: 'from apps.alpha_auth.models import Alpha_User\nprint(list(Alpha_User.objects.values()))\n',
    // code: 'import sys\nsys.path.append(\'/www/alpha/\')\n\nfrom icecream import ic\nfrom apps.__protobuf.alpha_grpc_stub import grpc_stub_function\n\nquery_dict = {\'a\': 3, \'b\': 4}\ngrpc_return = grpc_stub_function(\'gpu_std\', \'test\', \'plus\', query_dict)\n\nprint(grpc_return)',
    result: null,
    cmOptions: {
      tabSize: 4,
      styleActiveLine: true,
      lineNumbers: true,
      line: true,
      foldGutter: true,
      styleSelectedText: true,
      mode: 'text/x-python',
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
      this.$alphaTest.code.run(this.code).then(response => {
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
