<template>
  <v-dialog v-model="dialogVisible" persistent max-width="1400px">
    <template v-slot:activator="{ on, attrs }">
      <v-row fluid class="pa-0 ma-0 d-flex justify-end">
        <v-btn :on="on" :bind="attrs" @click="showDialog()" x-small text class="pr-3 ml-0 mr-n2 mt-2 primary--text">RUN Result</v-btn>
        <!-- <v-btn small color="white" :on="on" :bind="attrs" @click="showDialog()" outlined block>Prompt Engineering</v-btn> -->
      </v-row>
    </template>
    <v-card>
      <v-card-title
        class="primary white--text py-1 px-4 text-h6 font-weight-bold"
      >
        Run GPT Result
      </v-card-title>
      <v-card-text class="pt-0 pb-0 px-1">
        <v-container>
          <v-row class="pb-1">
            <v-col cols="1" class="font-weight-bold">Current Code</v-col>
            <!-- <v-col cols="11" class="font-weight-bold">{{doc._id}}</v-col> -->
          </v-row>
          <v-row v-for="(code, i) in codeList" :key="i">
            <v-col cols="12">
              <!-- <v-row class="" style="min-height: 560px;"> -->
              <codemirror v-model="code.code" :options="cmOptions"></codemirror>
              <!-- </v-row> -->
              <!-- <v-textarea background-color="#1E1E1E" class="custom-textarea font-weight-bold" v-model="code.code" filled auto-grow outlined hide-details></v-textarea> -->
              <v-row fluid class="pa-0 my-1 d-flex justify-end">
                <v-btn x-small color="primary" @click="runCode(code, i)">Run</v-btn>
              </v-row>
              <v-data-table v-if="code.result" dense :headers="code.headers" :items="code.result" :items-per-page="10"></v-data-table>
              <!-- <v-textarea v-if="code.result" background-color="#1E1E1E" class="custom-textarea font-weight-bold" v-model="code.result" filled auto-grow outlined hide-details></v-textarea> -->
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>
      <v-card-actions class="pt-0 pr-4 pb-4">
        <v-spacer></v-spacer>
        <slot name="custom-button"></slot>

        <!-- <v-btn
          small
          color="primary"
          outlined
          @click="deleteText"
        >
          Delete
        </v-btn> -->
        <v-btn
          small
          color="primary"
          outlined
          @click="cancel"
        >
          Cancel
        </v-btn>
      </v-card-actions>
    </v-card>

  </v-dialog>
</template>

<script>
// import { alphaGPT } from '@/_services'
// import { template, getDatetimeStringFromString } from '@/_helpers'

import { codemirror } from 'vue-codemirror'
import 'codemirror/lib/codemirror.css'

import 'codemirror/mode/sql/sql.js'
import 'codemirror/theme/vscode-dark.css'

// import 'codemirror/addon/selection/active-line.js'

// // styleSelectedText
import 'codemirror/addon/selection/mark-selection.js'
import 'codemirror/mode/clike/clike.js'

export default {
  props: {
    message: {
      type: String,
      required: true
    }
  },
  components: {
    // PrismEditor
    codemirror
  },
  data () {
    return {
      dialogVisible: false,
      dialogKey: 0,
      editMessage: '',
      codeList: [],
      cmOptions: {
        tabSize: 4,
        styleActiveLine: true,
        styleSelectedText: true,
        mode: 'text/x-pgsql',
        theme: 'vscode-dark',
        keyMap: 'sublime',
        matchBrackets: true,
        showCursorWhenSelecting: true
      }
    }
  },
  methods: {
    generateTextTable (data) {
      // Get the keys from the first object in the data array
      const headers = Object.keys(data[0])

      // Create a row for the headers
      const headerRow = headers.join(' | ')

      // Create a row for each object in the data array
      const rows = data.map((obj) => {
        return headers.map((header) => obj[header]).join(' | ')
      })

      // Combine the header row with the other rows to form the table
      return [headerRow, ...rows].join('\n')
    },
    runCode (code, i) {
      // console.log(this.code)
      this.result = null

      this.$alphaTest.sql.run(code.code).then(response => {
        // const resultTable = this.generateTextTable(response.data)
        // this.$set(this.codeList[i], 'result', resultTable)

        const keyList = Object.keys(response.data[0])
        code.headers = []

        for (let i = 0; i < keyList.length; i++) {
          const headerItem = { text: keyList[i], value: keyList[i], class: 'accent white--text', align: 'center' }
          code.headers.push(headerItem)
        }

        // this.$set(this.codeList[i], 'headers', response.data)
        this.$set(this.codeList[i], 'result', response.data)
      })
    },
    cancel () {
      this.dialogVisible = false
      this.$emit('cancel')
    },
    showDialog () {
      // console.log('show Dialog')
      this.dialogKey += 1
      this.dialogVisible = true
      this.$emit('showDialogValues', this.editType)
    }
  },
  mounted () {
    this.editMessage = this.message
    const regex = /```([\s\S]*?)```/g
    const matches = this.editMessage.match(regex)

    if (matches) {
      matches.forEach((match, index) => {
        const content = match.replace(/```/g, '')
        this.codeList.push({ code: content })
      })
    }
  }
}
</script>
