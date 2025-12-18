<template>
  <v-container fluid class="px-0 mt-0 pt-4" :style="{ background: $vuetify.theme.themes.light.background }">
      <v-row class="px-6">
        <div  style="font-weight: 600;" class="primary--text"> {{ testResult.test_unit_num }} : {{ testResult.test_unit_sub_num }}</div>
        &nbsp; |  &nbsp; {{ testResult.test_url }}&nbsp; :  &nbsp;{{ getTestAction }} &nbsp; |  &nbsp;
        {{ testResult.test_title }} &nbsp; |  &nbsp;
        <div  :style="{ color: textColor }">  <div  style="font-weight: 600;"> {{ successFail }}</div></div> &nbsp; |  &nbsp;
        {{ testResult.tester }},&nbsp;
        {{ testResult.created_on }}
        <v-btn class="ml-4" x-small :color="'secondary'" @click="deleteTestResult()">DELETE</v-btn>
      </v-row>
      <v-row class="px-6">
        <v-col cols="3" class="pr-1"><v-row><div class="ma-0 pa-0 text-caption">Request</div></v-row><v-row style="min-height: 240px;"></v-row></v-col>
        <v-col cols="3" class="px-1"><v-row><div class="ma-0 pa-0 text-caption">Response</div></v-row><v-row style="min-height: 240px;"></v-row></v-col>
        <v-col cols="3" class="px-1"><v-row><div class="ma-0 pa-0 text-caption">Test Code</div></v-row><v-row style="min-height: 240px;"></v-row></v-col>
        <v-col cols="3" class="pl-1"><v-row><div class="ma-0 pa-0 text-caption">Test Result</div></v-row><v-row style="min-height: 240px;"></v-row></v-col>
      </v-row>
      </v-container>
</template>

<script>
export default {
  name: 'backendTestResult',
  components: { },
  props: [
    'testResult'
  ],
  data () {
    return {

    }
  },
  computed: {
    getTestAction: {
      get () {
        // console.log(this.request)
        // const requestObject = JSON.parse(this.request)
        // const requestObject = this.request
        return this.request.action
      }
    },
    textColor: {
      get () {
        if (this.testResult.test_result === true) {
          return 'blue'
        } else {
          return 'red'
        }
      }
    },
    successFail: {
      get () {
        if (this.testResult.test_result === true) {
          return 'Success'
        } else {
          return 'Fail'
        }
      }
    },
    request: {
      get () {
        return JSON.stringify(this.testResult.request, null, 2)
      }
    },
    response: {
      get () {
        return JSON.stringify(this.testResult.response, null, 2)
      }
    }
  },
  methods: {
    itemTest (item) {
      console.log(item)
    },
    deleteTestResult () {
      this.$emit('deleteTestResult', this.testResult.id)
    }
  }
}
</script>

<style scoped>

.vue-codemirror {
  max-height: 240px !important;
  height: 240px !important;
}
</style>
