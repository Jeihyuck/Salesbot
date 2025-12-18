<template>
  <v-dialog width="1200" persistent v-model="isVisible">
      <v-card>
        <v-card-title dense class="white--text font-weight-black grey darken-2 px-6 py-1">
        Backend Error
        </v-card-title>
        <v-card-text class="pl-6 pt-4 pb-2 font-weight-black">시스템 관리자에게 다음 에러를 확인하시기 바랍니다. </v-card-text>
        <v-row class="px-6 py-0 mx-0 mt-0" style="min-height: 300px;">
          <codemirror v-model="errorCode" :options="cmOptions">
          </codemirror>
        </v-row>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="cancel">Cancel</v-btn>
        </v-card-actions>
      </v-card>
  </v-dialog>
</template>

<script>
import { mapState } from 'vuex'
import { codemirror } from 'vue-codemirror'
// import 'codemirror/lib/codemirror.css'

import 'codemirror/mode/python/python.js'
import 'codemirror/theme/vscode-dark.css'

export default {
  components: {
    codemirror
  },
  name: 'alphaBackendError',
  data () {
    return {
      // isVisible: false,
      // errorMsg: code,
      cmOptions: {
        tabSize: 4,
        // lineNumbers: true,
        line: true,
        mode: 'text/x-python',
        theme: 'vscode-dark',
        gutters: ['CodeMirror-linenumbers']
      }
    }
  },
  // watch: {
  //   isErrorMsg () {
  //     console.log('isErrorMsg')
  //     console.log(this.isErrorMsg)
  //   }
  // },
  computed: {
    ...mapState('backendError', ['isVisible']),
    ...mapState('backendError', ['errorMsg']),
    errorCode () {
      const code = this.errorMsg
      return code
    }
  },
  // computed: {

  // },
  methods: {
    // showBackendError () {
    //   this.errorMsg = this.$store.state.backendError.errorMsg
    // },
    cancel () {
      this.$store.dispatch('backendError/hideBackendError')
      // this.$store.state.backendError.isVisible = false
      // this.$store.state.backendError.errorMsg = ''
    }
  }
  // beforeMount () {
  //   alphaBackendErrorPlugIn.EventBus.$on('showBackendError', () => {
  //     console.log('params')
  //     // console.log(params)
  //     this.showBackendError()
  //   })
  // }
}

</script>

<style lang="css" scoped>

.CodeMirror-line {
  padding-left: 40px !important;
  margin-left: 40px !important;
}
</style>
