<template>
  <v-dialog width="1200" v-model="saveDialog">
      <template v-slot:activator="{ on }">
        <v-btn class="primary ml-2" small v-on="on">SAVE</v-btn>
      </template>
      <v-card>
        <v-card-title class="text-h5 grey lighten-2">
        SAVE : API Test Item
        </v-card-title>
        <v-card-text class="mt-0 mb-2 pb-0">
          <v-row>
            <v-col cols=4>
              <v-text-field label="작성자" class="mr-4" hide-details v-model="tempCreator"></v-text-field>
            </v-col>
            <v-col cols=8>
              <v-text-field label="제목" hide-details v-model="tempTitle"></v-text-field>
            </v-col>
          </v-row>
        <v-text-field label="비고" class="mb-4" hide-details v-model="tempDescription"></v-text-field>
        <!-- <v-text-field label="TEST URL" class="my-0 py-0" hide-details disabled v-model="testurl"></v-text-field> -->
        <v-card-text class="pl-1 pb-1 font-weight-black"> Request </v-card-text>
        <!-- <v-card-text class="pa-0" v-html="requestHTML"></v-card-text> -->
        <prism-editor
          class="prismEditor"
          v-model="tempRequest"
          :highlight="highlighter"
          style="height: 200px;"
          line-numbers
        ></prism-editor>
        <v-card-text class="mt-0 pl-1 pb-1 font-weight-black"> Response </v-card-text>
        <prism-editor
          class="prismEditor"
          v-model="tempResponse"
          :highlight="highlighter"
          style="height: 200px;"
          line-numbers
        ></prism-editor>
        <!-- <v-card-text class="pa-0" v-html="responseHTML"></v-card-text> -->
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="saveAPI">Save</v-btn>
          <v-btn color="primary" text @click="cancel">Cancel</v-btn>
        </v-card-actions>
      </v-card>
  </v-dialog>
</template>

<script>
import { alphaTest } from '@/_services'


export default {
  components: {
  },
  name: 'SaveDialog',
  props: ['testurl', 'apiurlprefix', 'creator', 'testTitle', 'description', 'request', 'response'],
  data () {
    return {
      tempCreator: null,
      tempTitle: null,
      tempDescription: null,
      saveDialog: false,
      backendTest: false,
      tempRequest: '',
      tempResponse: '',
      // requestjsontext: '',
      // responsejsontext: '',
      // requestHTML: '',
      // responseHTML: '',
      editItem: null
    }
  },
  watch: {
    saveDialog () {
      if (this.saveDialog === true) {
        this.tempCreator = this.creator
        this.tempTitle = this.testTitle
        this.tempDescription = this.description
        this.tempRequest = this.request
        this.tempResponse = this.response
      }
    }
  },
  methods: {
    highlighter (code) {
      return highlight(code, languages.json)
    },
    cancel () {
      this.saveDialog = false
      this.requestjsontext = ''
      this.responsejsontext = ''
      this.requestHTML = ''
      this.responseHTML = ''
    },
    saveAPI () {
      if (this.tempCreator === '' || this.tempCreator === undefined || this.tempTitle === '' || this.tempTitle === undefined) {
        alert('작성자 이름과 제목을 입력하세요.')
      } else {
        if (this.tempResponse === undefined) {
          this.tempResponse = '{}'
          // alert('Response 값이 없습니다.')
        }

        const query = {
          creator: this.tempCreator,
          test_title: this.tempTitle,
          description: this.tempDescription,
          testurl: this.testurl.replace(this.apiurlprefix, ''),
          requestjsontext: this.tempRequest,
          responsejsontext: this.tempResponse
        }
        alphaTest.api.api('create', query)
        // alphaTest.api.api('create', query).then(response => {
        //   console.log(response)
        // })
        this.saveDialog = false
      }
    }
  }
}

</script>


