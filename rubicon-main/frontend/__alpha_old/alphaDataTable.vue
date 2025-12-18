<template>
  <div>
    <!--  -->
  <v-data-table
    dense
    v-model="selected"
    :hide-default-header="alphaModel.customHeader"
    :show-select="alphaModel.showSelect === undefined ? false : alphaModel.showSelect"
    :hide-default-footer="!alphaModel.pagination"
    :items-per-page="options.itemsPerPage"
    :headers="headers"
    :items="filteredTableData"
    :options.sync="options"
    :loading="loadingStatus"
    :server-items-length="serverItemsLength"
    :footer-props="{
      'items-per-page-options': paginationOption,
      'show-current-page' : true,
      'showFirstLastPage': true,
      'items-per-page-text': ''
    }"
    item-key="index"
    class="elevation-1 alphaDataTable"
    @page-count="pageCount = $event"
    @click:row="onClickRow"
    :key="tableKey"
  >
    <template
        v-for="(header, i) in headers"
        v-slot:[`header.${header.value}`]="{ }"
      >
        {{ header.text }}
        <div @click.stop :key="i" v-if="alphaModel.columnFilter" >
          <alpha-text-input-field-in-table :key="i"
            v-model="multiSearch[header.value]"
            class="pa"
            type="text"
            color="primary"
            :placeholder="header.value"></alpha-text-input-field-in-table>
        </div>
    </template>

    <template v-if="alphaModel.customHeader === true" slot="header" >
      <slot name="custom-header"></slot>
    </template>
    <template v-for="field in alphaModel.customFields" v-slot:[`item.${field}`]="{ item }">
      <slot :name="`${field}_custom`" v-bind:item="item"></slot>
    </template>

    <template v-slot:item.action="{ item }">
      <!-- <slot v-if="!putCustomInTheMiddle" v-bind:item="item" name="table_custom_action"></slot> -->
      <slot v-bind:item="item" name="table_custom_action"></slot>
      <alphaDataTable-dialog-wrapper
        x-small
        outlined
        v-if="alphaModel.crud[2]"
        :editType="`EDIT`"
        :alphaModel="alphaModel"
        @showDialogValues="showDialogValues($event, item)"
        @update="update"
        @cancel="cancel"
      >
        <template v-slot:custom="{ slotName }">
          <slot name="custom" :slotName="slotName"></slot>
        </template>
      </alphaDataTable-dialog-wrapper>
      <alpha-btn v-if="alphaModel.crud[3]" outlined x-small :color="'primary'" :value="'DELETE'" :minimize="true" @click="deleteItem(item.index, item)"></alpha-btn>
    </template>
  </v-data-table>
  <alphaConfirm :key="deletionConfirmKey" ref="deleteConfirm" />
  </div>
</template>
<script>
import alphaTextInputFieldInTable from '@/components/alpha/alphaTextInputFieldInTable'
import { addIndexToArray, notify } from '@/_helpers'
import alphaDataTableDialogWrapper from '@/components/alpha/alphaDataTableDialogWrapper'

export default {
  name: 'alphaDataTable',
  components: {
    alphaDataTableDialogWrapper,
    alphaTextInputFieldInTable,
    alphaConfirm: () => import('@/components/alpha/alphaConfirm')
  },
  data () {
    return {
      query: {},
      paging: {},
      requestCount: 0,
      multiSearch: {},
      showPopupMenu: false,
      loaded: false,
      options: null,
      totalItemCount: 0,

      page: 1,

      tableData: [],
      headers: [],
      selected: [],

      deleteList: [],
      clickDelete: false,
      deletionConfirmKey: 10000,
      tableKey: 0
    }
  },
  props: [
    'alphaModel',
    'showDialogValues',
    'update',
    'cancel',
    'putCustomInTheMiddle'
  ],
  watch: {
    'options.page': {
      deep: true,
      handler () {
        // console.log('load page')
        if (this.requestCount === 0) {
          this.tableData = []
          this.requestTableData(this.alphaModel)
        }
        if (this.requestCount !== 0 && (this.alphaModel.fullLoad === undefined || this.alphaModel.fullLoad === false)) {
          this.tableData = []
          this.requestTableData(this.alphaModel)
        }
        this.requestCount = this.requestCount + 1
      }
    }
  },
  computed: {
    loadingStatus () {
      if (this.loaded === true) {
        return false
      } else {
        if (this.alphaModel.showLoading !== false) {
          return true
        } else {
          return false
        }
      }
    },
    paginationOption () {
      if (this.alphaModel.paginationOption) {
        return this.alphaModel.paginationOption
      } else {
        return [15, 30]
      }
    },
    serverItemsLength () {
      if (this.alphaModel.pagination === true && (this.alphaModel.fullLoad === undefined || this.alphaModel.fullLoad === false)) {
        return this.totalItemCount
      } else {
        return -1
      }
    },
    filteredTableData () {
      if (this.multiSearch) {
        return this.tableData.filter((item) => {
          return Object.entries(this.multiSearch).every(([key, value]) => {
            if (value.includes('|') && !value.includes('!')) {
              const el = value.split('|')
              return el.some((elem) =>
                (item[key] || '').toString().toUpperCase().startsWith(elem.toString().toUpperCase())
              )
            }
            if (value.substring(0, 1) === '!' && !value.includes('|')) {
              const el = value.split('!')
              return el.some((elem) =>
                !(item[key] || '').toString().toUpperCase().startsWith(elem.toString().toUpperCase())
              )
            }
            if (value.includes('|') && value.substring(0, 1) === '!') {
              const el = value.split('!')[1].split('|')
              return !el.some((elem) =>
                (item[key] || '').toString().toUpperCase().startsWith(elem.toString().toUpperCase())
              )
            }
            if (value.substring(0, 1) === '>') {
              const el = value.split('>')
              if (item[key] !== ' ') {
                return Number(item[key] || '') > el[1]
              }
            }
            if (value.substring(0, 1) === '<') {
              const el = value.split('<')
              if (item[key] !== ' ') {
                return Number(item[key] || '') < el[1]
              }
            }
            if (value.substring(0, 1) === '=') {
              const el = value.split('=')
              return (item[key] || '').toString().toUpperCase() === el[1].toString().toUpperCase()
            }
            return (item[key] || '').toString().toUpperCase().includes(value.toString().toUpperCase())
          })
        })
      } else {
        return this.tableData
      }
    }
  },
  created () {
    if (this.alphaModel.pagination === true) {
      if (this.alphaModel.paginationOption) {
        this.options = { page: 1, itemsPerPage: this.alphaModel.paginationOption[0] }
      } else {
        this.options = { page: 1, itemsPerPage: 15 }
      }
    } else {
      this.options = { page: 1, itemsPerPage: 100000 }
    }

    // if ('sortBy' in this.alphaModel) {
    //   this.options.sortBy = this.alphaModel.sortBy
    //   this.options.sortDesc = this.alphaModel.sortDesc
    // }
    // document.body.addEventListener('click', this.__handlerRef__)
  },
  destroyed () {
    // document.body.removeEventListener('click', this.__handlerRef__)
  },
  methods: {
    requestData (alphaModel) {
      if (alphaModel.fullLoad === undefined) {
        alphaModel.fullLoad = false
      }
      this.paging = {
        page: parseInt(this.options.page),
        itemsPerPage: this.options.itemsPerPage,
        fullLoad: alphaModel.fullLoad
      }
      this.query = {}
      for (const key in alphaModel.filter) {
        if (alphaModel.filter[key].selected !== undefined && alphaModel.filter[key].selected !== null && this.alphaModel.filter[key].selected !== '') {
          this.query[key] = alphaModel.filter[key].selected
        }
      }
      if (alphaModel.injectedQuery) {
        this.query.injectedQuery = alphaModel.injectedQuery
      }
      return alphaModel.function('read', this.query, this.paging)
    },
    async deleteRequestData (alphaModel, id) {
      return alphaModel.function('delete', { id: id, filter: alphaModel.filter })
    },
    // stringifyNestedObjects (obj) {
    //   for (const prop in obj) {
    //     if (typeof obj[prop] === 'object' && obj[prop] !== null) {
    //       obj[prop] = JSON.stringify(obj[prop])
    //     }
    //   }
    //   return obj
    // },
    requestTableData (alphaModel, searchByButton = false) {
      if (searchByButton) {
        this.$set(this.options, 'page', 1)
      }
      if (alphaModel.headerId !== 'custom-header') {
        this.$alpha.table.getTableHeader(alphaModel.headerId).then(response => {
          this.headers = []
          this.headers = response.data
          this.alphaModel.headerField = []
          for (let i = 0; i < response.data.length; i++) {
            this.alphaModel.headerField.push(response.data[i].value)
          }
        })
      }

      if (this.alphaModel.function !== undefined) {
        this.requestData(alphaModel).then(response => {
          this.loaded = true
          if (response.success && response.data !== null) {
            this.tableData = []
            // for (let i = 0; i < response.data.length; i++) {
            //   response.data[i] = this.stringifyNestedObjects(response.data[i])
            // }

            if (alphaModel.sort) {
              response.data.sort(alphaModel.sort)
            }
            this.tableData = addIndexToArray(response.data, (this.options.page - 1) * this.options.itemsPerPage + 1)
            if (response.meta[0]) {
              this.totalItemCount = response.meta[0].itemCount
            }
          }
        })
      }
    },
    async deleteItem (itemIndex, item) {
      if (
        await this.$refs.deleteConfirm.open(
          'Confirm',
          '삭제하시겠습니까?'
        )
      ) {
        this.deleteRequestData(this.alphaModel, item.id).then(response => {
          if (response.success === true) {
            notify.SUCCESS(this, this.alphaModel.name + '(이)가 삭제되었습니다.')
          } else {
            notify.ERROR(this, '삭제를 실패하였습니다.')
          }
        }).then(() => {
          this.deletionConfirmKey = this.deletionConfirmKey + 1
          this.requestTableData(this.alphaModel)
        })
      }
      this.tableKey += 1
    },
    onClickRow (row) {
      this.$emit('click:row', row)
    },
    getSelected () {
      const selectedIdList = this.selected.map(obj => obj.id)
      const result = this.tableData.filter(obj => selectedIdList.includes(obj.id))
      return result
    }
  }
}
</script>

<style lang="sass">
  @import '@/alphaColors.scss'
  @import '~@/components/alpha/styles/alphaTextStyles.scss'
</style>

<style scoped>
.v-data-table > .v-data-table__wrapper {
  overflow: unset !important;
}

.v-data-table > .v-data-table__wrapper > table > thead > tr > .sticky-header {
  position: sticky !important;
  top: var(--titleHeight);
}
</style>
