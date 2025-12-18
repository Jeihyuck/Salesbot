<template>
  <alphaDataTableDialog :alphaModel="apiTestLoad" ref="dialog" >
    <template v-slot:table-custom-action="{ item }">
      <alpha-btn outlined x-small :color="'primary'" :value="'Load API'" :minimize="true" @click="loadAPI(item)"></alpha-btn>
    </template>
  </alphaDataTableDialog>
</template>

<script>
import { alphaTest } from '@/_services'
import alphaDataTableDialog from '@/components/alpha/alphaDataTableDialog'

export default {
  name: 'LoadDialog',
  components: { alphaDataTableDialog },
  data () {
    return {
      apiTestLoad: {
        dialog: {
          btnText: 'Load And Manage',
          title: 'Load : API Test Item',
          width: 8,
          // dialogVisible: false,
          items: [
            {
              type: 'dataTableView',
              model: {
                name: 'apiLoadTable',
                function: alphaTest.api.api,
                crud: [false, true, false, true],
                headerId: '1ea696fb-3fca-45de-985f-ddcfcb6dad2e',
                pagination: true,
                fullLoad: true,
                columnFilter: true,
                customFields: [],
                filter: {
                  hideBoarder: true,
                  search: {
                    name: '검색',
                    type: 'search',
                    selected: '',
                    col: 6
                  }
                }
              }
            }
          ]
        }
      }
    }
  },
  computed: {
    backendTestColor: {
      get () {
        if (this.selectedBackendTest === 'Y') {
          return 'black'
        }
        return 'primary'
      }
    }
  },
  methods: {
    rowClick (item, row) {
      row.select(true)
      this.selectedAPI = item.id
      this.selectedBackendTest = item.backend_test
    },
    loadAPI (item) {
      // console.log(item)
      // this.apiTestLoad.dialog.dialogVisible = false
      this.$refs.dialog.cancel()
      this.$emit('loadAPI', item.id)
    },
    deleteAPI () {
      const query = { uuid: this.selectedAPI }
      alphaTest.api.api('delete', query).then(response => {
        if (response.success) {
          this.readAPI()
        }
        this.selectedAPI = null
        this.selectedBackendTest = null
      })
    },
    readAPI () {
      this.paging = {
        page: parseInt(this.options.page),
        itemsPerPage: this.options.itemsPerPage
      }
      alphaTest.api.api('read', {}, this.paging).then(response => {
        if (response.success) {
          this.tableData = response.data
          this.totalItemCount = response.meta[0].itemCount
        }
      })
    }
    // cancel () {
    //   this.apiTestLoad.dialog.dialogVisible = false
    // }
  }
}
</script>

