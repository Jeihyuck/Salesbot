<template>
  <v-container fluid class="px-0 mt-0 pt-4" :style="{ background: $vuetify.theme.themes.light.background }">
    <v-row class="px-6 py-0 my-0 mx-0 d-flex justify-end">
      <v-btn @click="reloadTable" small class="mr-2 info">
        Load Test Items
      </v-btn>
      <v-btn @click="clearTestResult" small class="mr-0 info">
        Clear Test Result
      </v-btn>
    </v-row>

    <alpha-data-table-view ref="backendTestItems" :key="tableKey" :alphaModel="testItems" @search="onSearch" class="pa-6">
      <template v-slot:table-buttons="{}">
        <v-btn @click="backendTest" small :color="'primary'" class="mr-0">
          Test
        </v-btn>
      </template>
      <template v-slot:table-custom-action="{ item }">
        <alpha-btn x-small :color="'secondary'" :value="'TEST'" :minimize="true" @click="itemTest(item)"></alpha-btn>
        <alpha-btn outlined x-small :color="'secondary'" :value="'COPY'" :minimize="true" @click="copyTestItem(item)"></alpha-btn>
      </template>
      <template v-slot:test_action_custom="{ item }">
        <div> {{ getTestAction(item) }}</div>
      </template>
      <template v-slot:backend_test_custom="{ item }">
        <div> {{ item.backend_test? 'Y':'-' }}</div>
      </template>
    </alpha-data-table-view>

    <v-row class="px-6 py-0 my-0 mx-0">
      <div>Test Result</div>
    </v-row>
    <v-row class="px-6">
      <v-divider></v-divider>
    </v-row>
    <div v-for="testResult of testResults" :key="testResult.test_unit_num.toString() + ':' + testResult.test_unit_sub_num.toString()">
      <backend-test-result :testResult="testResult" @deleteTestResult="deleteTestResult"></backend-test-result>
    </div>
  </v-container>
</template>

<script>
import alphaDataTableView from '@/components/alpha/alphaDataTableView'
import backendTestResult from '@/pages/__alpha/test/backendTestResult'
import { template } from '@/_helpers'
import { alphaTest } from '@/_services'

export default {
  name: 'backendTest',
  components: { alphaDataTableView, backendTestResult },
  data () {
    return {
      tableKey: 0,
      testResults: [],
      testItems: {
        name: 'Backend Test Item',
        function: alphaTest.api.backendTest,
        crud: [false, true, true, true],
        headerId: 'bed25913-7107-45f6-a003-1bafaca99d42',
        pagination: false,
        fullLoad: true,
        sortBy: ['test_url', 'test_seq'],
        sortDesc: [false, false],
        customFields: ['backend_test', 'test_action'],
        hideMiddle: true,
        showSelect: true,
        dataMap: {
          is_admin: (row) => {
            row.is_admin = row.is_admin === true ? 'Y' : '-'
          }
        },
        filter: {
          hideBoarder: false,
          testUrl: {
            name: 'Test URL',
            type: 'dropdown',
            clearable: true,
            multiple: true,
            selector: [],
            selected: '',
            col: 5
          },
          searchScope: {
            name: '',
            type: 'radio',
            selector: [{ text: '전체', value: 'all' }, { text: 'Backend Test', value: 'backend_test' }],
            selected: 'backend_test',
            col: 2
          },
          testResultSize: {
            name: 'Test Result Size',
            type: 'dropdown',
            clearable: true,
            selector: [1, 2, 3, 4, 5, 'all'],
            selected: 3,
            col: 1
          },
          tester: {
            name: 'Tester',
            type: 'dropdown',
            multiple: true,
            clearable: true,
            selector: [],
            selected: '',
            col: 2
          }
        },
        dialogWidth: '800px',
        dialog: {
          test_title: template.fields.REQUIRED_INPUT('Title'),
          test_url: template.fields.REQUIRED_INPUT('Test URL'),
          test_seq: template.fields.OPTIONAL_INPUT('Test Seq'),
          creator: template.fields.REQUIRED_INPUT('Creator'),
          description: template.fields.OPTIONAL_INPUT('Description'),
          backend_test: {
            name: 'Unit Test',
            type: 'dropdown',
            multiple: false,
            disabled: () => {
              return false
            },
            required: true,
            selector: [{ text: 'Y', value: true }, { text: 'N', value: false }],
            selected: ''
          },
          request: {
            name: 'Request',
            type: 'code',
            disabled: () => {
              return false
            },
            language: 'json',
            selected: ''
          },
          response: {
            name: 'Resopnse',
            type: 'code',
            disabled: () => {
              return false
            },
            language: 'json',
            selected: ''
          },
          test_code: {
            name: 'Test Code',
            type: 'code',
            disabled: () => {
              return false
            },
            language: 'python',
            selected: ''
          }
        }
      }
    }
  },
  methods: {
    getTestUnitNum (testUnitNum, testUnitSubNum) {
      console.log(testUnitNum, testUnitSubNum)
    },
    async itemTest (item, testUnitNum = null, testUnitSubNum = null) {
      await this.$serviceAlpha.stdPostFunction(
        item.test_url,
        // JSON.parse(item.request)
        item.request
      ).then(response => {
        const testResponse = { id: item.id, response: response }
        return testResponse
      }).then(response => {
        let query = ''
        if (testUnitNum !== null && testUnitSubNum != null) {
          query = { id: response.id, response: response.response, test_code: item.test_code, test_unit_num: testUnitNum, test_unit_sub_num: testUnitSubNum }
        } else {
          query = { id: response.id, response: response.response, test_code: item.test_code }
        }
        this.$alphaTest.api.backendTest('backendTest', query, {}).then(() => {
          this.queryBackendTestResult()
        })
      })
    },
    copyTestItem (item) {
      const query = { id: item.id }
      alphaTest.api.backendTest('copy', query, {})
      this.$refs.backendTestItems.onSearch()
    },
    reloadTable () {
      this.tableKey += 1
    },
    clearTestResult () {
      alphaTest.api.backendTest('clearBackendTestResult').then(response => {
        this.queryBackendTestResult()
      })
    },
    async backendTest () {
      alphaTest.api.backendTest('getCurrentBackendTestUnitNum').then(response => {
        const selected = this.$refs.backendTestItems.getSelected()
        selected.sort((a, b) => {
          if (a.test_seq < b.test_seq) {
            return -1
          }
          if (a.test_seq > b.test_seq) {
            return 1
          }
          if (a.test_url < b.test_url) {
            return -1
          }
          if (a.test_url > b.test_url) {
            return 1
          }
          return 0
        })

        return { selected: selected, testUnitNum: response.data }
      }).then(async (response) => {
        for (let i = 0; i < response.selected.length; i++) {
          await this.itemTest(response.selected[i], response.testUnitNum, i + 1)
        }
      }).then(() => {
        alphaTest.api.getTester().then(response => {
          this.testItems.filter.tester.selector = response.data
        })
      })
    },
    onSearch () {
      this.queryBackendTestResult()
    },
    queryBackendTestResult () {
      const query = { size: this.testItems.filter.testResultSize.selected, tester: this.testItems.filter.tester.selected }
      alphaTest.api.backendTest('getBackendTestResult', query, {}).then(response => {
        // console.log(response)
        this.testResults = response.data
      })
    },
    deleteTestResult (id) {
      const query = { id: id }
      alphaTest.api.backendTest('deleteTestResult', query, {}).then(response => {
        this.queryBackendTestResult()
      })
    },
    getTestAction (item) {
      // console.log(item)
      // const request = JSON.parse(item.request)
      // item.test_action = request.action
      return item.request.action
    }
  },
  mounted () {
    alphaTest.api.getTestUrls().then(response => {
      this.testItems.filter.testUrl.selector = response.data
    })
    alphaTest.api.getTester().then(response => {
      this.testItems.filter.tester.selector = response.data
    })
    this.queryBackendTestResult()
  }
}
</script>
