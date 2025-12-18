<template>
  <!-- <v-col class="ma-0 pa-0"> -->
    <!-- <v-row class="mb-2">
      <v-col cols="12" class="pa-0">
      <v-card class="w-100">
      <v-row>
        <v-col cols="11">
          <v-row class="pa-3">
            <v-col cols="3">
              <v-combobox
                label="Autocomplete"
                variant="outlined"
                density="compact"
                base-color="grey-darken-1"
                hide-details
                multiple
                :items="['California', 'Colorado', 'Florida', 'Georgia', 'Texas', 'Wyoming']"
              ></v-combobox>
            </v-col>
          </v-row>
        </v-col>
        <v-col cols="1">
          <v-row class="pa-3">
            <v-col>
              <v-btn class="mt-1" color="primary">Search</v-btn>
            </v-col>
          </v-row>
        </v-col>
        </v-row>
      </v-card>
      </v-col>
    </v-row>
    <v-row>

    </v-row> -->
    <alphaDataTable-view :alphaModel="alphaModel"></alphaDataTable-view>
  <!-- </v-col> -->
</template>

<script>
import { alphaExample } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'
// import { addIndexToArray, notify } from '@/_helpers'

export default {
  components: {
    alphaConfirm: () => import('@/components/alpha/alphaConfirm'),
    alphaDataTableView
  },
  data: () => ({
    alphaModel: {
      tableUniqueID: 'ex12',
      paging: { page: 1, itemsPerPage: 5 },
      function: alphaExample.ex12.ex12Function,
      crud: [false, true, false, false],
      headerId: 'ca84889e-de87-4757-b2b2-a9fd3c5635db'
    },
  }),
  methods: {
    // test () {
    //   this.requestTableData()
    //   // this.tableMetaStore.page[this.tableID] = 1
    //   // this.tableMetaStore.items[this.tableID] = ['1', '2', '3']
    //   // console.log(this.tableMetaStore.page)
    //   // console.log(this.tableMetaStore.items)
    //   // this.tableMetaStore.page['ex23'] = 1
    //   // console.log(this.tableMetaStore.page)
    // },
    // requestTableData (searchByButton = false) {
    //   if (searchByButton) {
    //     this.$set(this.options, 'page', 1)
    //   }
    //   if (this.alphaModel.headerId !== 'custom-header') {
    //     alpha.table.getTableHeader(this.alphaModel.headerId).then(response => {
    //       this.headers = []
    //       this.headers = response.data
    //       this.alphaModel.headerField = []
    //       for (let i = 0; i < response.data.length; i++) {
    //         this.alphaModel.headerField.push(response.data[i].value)
    //       }
    //     })
    //   }

    //   if (this.alphaModel.function !== undefined) {
    //     this.requestData().then(response => {
    //       this.loaded = true
    //       if (response.success && response.data !== null) {
    //         this.tableData = []
    //         // for (let i = 0; i < response.data.length; i++) {
    //         //   response.data[i] = this.stringifyNestedObjects(response.data[i])
    //         // }

    //         if (this.alphaModel.sort) {
    //           response.data.sort(alphaModel.sort)
    //         }
    //         this.tableData = addIndexToArray(response.data, (this.options.page - 1) * this.options.itemsPerPage + 1)
    //         if (response.meta[0]) {
    //           this.totalItemCount = response.meta[0].itemCount
    //         }
    //       }
    //     })
    //   }
    // },
    // requestData () {
    //   if (this.alphaModel.fullLoad === undefined) {
    //     this.alphaModel.fullLoad = false
    //   }
    //   this.paging = {
    //     page: parseInt(this.options.page),
    //     itemsPerPage: this.options.itemsPerPage,
    //     fullLoad: this.alphaModel.fullLoad
    //   }
    //   this.query = {}
    //   // for (const key in this.alphaModel.filter) {
    //   //   if (this.alphaModel.filter[key].selected !== undefined && this.alphaModel.filter[key].selected !== null && this.this.alphaModel.filter[key].selected !== '') {
    //   //     this.query[key] = this.alphaModel.filter[key].selected
    //   //   }
    //   // }
    //   // if (this.alphaModel.injectedQuery) {
    //   //   this.query.injectedQuery = this.alphaModel.injectedQuery
    //   // }
    //   return this.alphaModel.function('read', this.query, this.paging)
    // },
    // requestHeader () {

    // },
    // async deleteItem (itemIndex, item) {
    //   if (
    //     await this.$refs.deleteConfirm.open(
    //       'Confirm',
    //       '삭제하시겠습니까?'
    //     )
    //   ) {
    //     this.deleteRequestData(this.alphaModel, item.id).then(response => {
    //       if (response.success === true) {
    //         notify.SUCCESS(this, this.alphaModel.name + '(이)가 삭제되었습니다.')
    //       } else {
    //         notify.ERROR(this, '삭제를 실패하였습니다.')
    //       }
    //     }).then(() => {
    //       this.deletionConfirmKey = this.deletionConfirmKey + 1
    //       this.requestTableData(this.alphaModel)
    //     })
    //   }
    //   this.tableKey += 1
    // },
    // onClickRow (row) {
    //   this.$emit('click:row', row)
    // },
    // getSelected () {
    //   const selectedIdList = this.selected.map(obj => obj.id)
    //   const result = this.tableData.filter(obj => selectedIdList.includes(obj.id))
    //   return result
    // }
  },
}
</script>