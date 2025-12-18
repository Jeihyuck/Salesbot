<template>
  <v-container fluid class="px-0 mt-0 pt-4" :style="{ background: $vuetify.theme.themes.light.background }">
    <v-row class="px-8 pt-2 pb-0 my-0 mx-0 d-flex justify-end">
      <set-api-key :apiKey="apiKey" @saveApiKey="saveApiKey"></set-api-key>
      <api-test-load v-on:loadAPI="loadAPI"></api-test-load>
      <api-test-save :testurl="testurl" :creator="creator" :testTitle="testTitle" :description="description" :request="request" :response="response"></api-test-save>
    </v-row>
    <v-row class="px-8 pt-0 pb-2 mx-0 mt-0" >
      <v-text-field label="TEST URL" hide-details v-model="testurl"></v-text-field>
    </v-row>
    <v-row class="px-8 mx-0">
      <div style="font-weight: 800;">Request</div>
    </v-row>
    <v-row class="px-8 pt-0 pb-4 mx-0" style="min-height: 300px;">
      <!-- <codemirror v-model="request" :options="cmOptions">
      </codemirror> -->
    </v-row>
    <v-row class="px-8 pt-2 pb-0 my-0 mx-0 d-flex justify-end">
      <v-btn @click="executeRequest" small class="primary ml-2">
        Request
      </v-btn>
    </v-row>
    <v-row class="px-8 mx-0 pt-0">
      <div style="font-weight: 800;">Response</div>
    </v-row>
    <v-row class="px-8 pt-0 pb-0 mx-0" style="min-height: 320px;">
      <!-- <codemirror v-model="response" :options="cmOptions">
      </codemirror> -->
    </v-row>
    <simple-loader></simple-loader>
  </v-container>
</template>

<script>

import setApiKey from '@/pages/__alpha/test/setApiKey'
import apiTestSave from '@/pages/__alpha/test/apiTestSave'
import apiTestLoad from '@/pages/__alpha/test/apiTestLoad'

export default {
  components: {
    codemirror, setApiKey, apiTestSave, apiTestLoad
  },
  data () {
    return {
      lineNumbers: true,
      apiKey: null,
      creator: '',
      testTitle: '',
      description: '',
      testurl: '',
      request: '',
      response: '',
      initialRequestValue: {
        action: 'ACTION',
        query: { data: [1, 2, 3, 4] }
      },
      initialResponseValue: {
        result: 'NOT YET EXECTUED'
      },
      cmOptions: {
        tabSize: 2,
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
    }
  },
  methods: {
    executeRequest () {
      this.$simpleLoaderPlugIn.show()
      // 'Authorization': 'Api-Key GDMv2DIP.KE8R8MXnEdmBXzeodGxNyh2UJJm1dGSr'
      this.testJSON = this.request
      this.$serviceAlpha.stdPostFunction(
        this.testurl,
        JSON.parse(this.testJSON),
        this.apiKey
      ).then(response => {
        this.response = JSON.stringify(response, null, 2)
        this.$simpleLoaderPlugIn.hide()
      })
    },
    saveApiKey (apiKey) {
      console.log(apiKey)
      this.apiKey = apiKey
    },
    loadAPI (uuid) {
      const query = { uuid: uuid }
      this.$alphaTest.api.api('readItem', query).then(response => {
        if (response.success) {
          this.testurl = response.data.test_url
          this.request = JSON.stringify(response.data.request, null, 2)
          this.response = JSON.stringify(response.data.response, null, 2)
          this.creator = response.data.creator
          this.testTitle = response.data.test_title
          this.description = response.data.description
        }
      })
    }
  },
  mounted () {
    this.request = JSON.stringify(this.initialRequestValue, null, 2)
    this.response = JSON.stringify(this.initialResponseValue, null, 2)
  }
}
</script>``

