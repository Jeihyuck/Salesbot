<template>
  <div :style="{ background: $vuetify.theme.themes.light.background }">
    <v-container fluid class="pa-0 ma-0">
      <alphaFilter
        v-if="alphaModel.filter"
        :alphaModel="alphaModel"
        v-on:update:filter="onUpdateFilter"
        v-on:click:filter="onSearch"
      />
    </v-container>
    <v-container fluid class="pa-0 ma-0 d-flex justify-end" v-if="alphaModel.hideMiddle !== false || alphaModel.hideMiddle !== undefined">
      <slot name="table-buttons"></slot>
      <v-btn
        v-if="hasDownload"
        style="margin: 0px 0px 1px 0px"
        color="primary"
        small
        @click="excelDownload()"
        >엑셀 다운로드</v-btn>
      <alphaDataTable-dialog-wrapper
      v-if="alphaModel.crud[0]"
      small
      :editType="`CREATE`"
      :alphaModel="alphaModel"
      @showDialogValues="showDialogValues"
      @update="update"
      @cancel="cancel"
      >
      </alphaDataTable-dialog-wrapper>
    </v-container>

    <v-container fluid class="pa-0 ma-0">
      <alphaDataTable
      class="mt-1"
      ref="dataTable"
      :alphaModel="alphaModel"
      :showDialogValues="showDialogValues"
      :update="update"
      :cancel="cancel"
      :putCustomInTheMiddle="putCustomInTheMiddle"
    >
      <template v-slot:custom-header>
        <slot v-if="alphaModel.customHeader === true" name="custom-header"></slot>
      </template>
      <template v-for="field in alphaModel.customFields" v-slot:[`${field}_custom`]="{ item }">
        <slot :name="`${field}_custom`" v-bind:item="item" />
      </template>
      <template v-slot:table_custom_action="{ item }">
        <slot name="table_custom_action" :item="item"></slot>
      </template>
    </alphaDataTable>
    </v-container>
    <slot name="custom-component"></slot>
  </div>
</template>

<script>
import { uuid } from 'vue-uuid'
import alphaDataTable from '@/components/alpha/alphaDataTable.vue'
import alphaFilter from '@/components/alpha/alphaFilter'
import alphaDataTableDialogWrapper from '@/components/alpha/alphaDataTableDialogWrapper'
export default {
  components: {
    alphaFilter,
    alphaDataTable,
    alphaDataTableDialogWrapper
  },
  props: {
    alphaModel: Object,
    putCustomInTheMiddle: {
      type: Boolean,
      default: false
    }
  },
  data () {
    return {
      updateSuccess: true
    }
  },
  computed: {
    hasDownload: {
      get () {
        if (this.alphaModel.excel !== undefined) {
          if (this.alphaModel.excel.download !== undefined) {
            return true
          } else {
            return false
          }
        } else {
          return false
        }
      }
    }
  },
  methods: {
    onUpdateFilter (v) {
      this.$set(this.alphaModel.filter[v.key], 'selected', v.value)
    },
    excelDownload () {
      const query = {}
      const jobUUID = uuid.v4()

      for (const key in this.alphaModel.filter) {
        if (this.alphaModel.filter[key].selected !== undefined && this.alphaModel.filter[key].selected !== null && this.alphaModel.filter[key].selected !== '') {
          query[key] = this.alphaModel.filter[key].selected
        }
      }

      this.$alpha.util.excelDownload(
        jobUUID,
        this.alphaModel.excel.download.fuctionUrl,
        this.alphaModel.excel.download.action,
        query,
        this.alphaModel.excel.download.template
      ).then(() => {
        const fileName = jobUUID + '.xlsx'
        this.$serviceAlpha.getFile(fileName, this.alphaModel.excel.download.filename)
      })
    },
    onSearch () {
      this.$refs.dataTable.requestTableData(this.alphaModel, true)
      this.$emit('search')
    },
    getSelected () {
      return this.$refs.dataTable.getSelected()
      // const a = 2
      // return a
    },
    showDialogValues (editType, editingRowData) {
      if (editType === 'CREATE') {
        for (const [key, value] of Object.entries(this.alphaModel.dialog)) {
          if (this.alphaModel.filter) {
            const filter = Object.keys(this.alphaModel.filter).includes(
              key.toLowerCase()
            )
              ? this.alphaModel.filter[key.toLowerCase()].selected
              : ''
            if (Array.isArray(filter) && filter.length > 1) {
              value.selected = ''
            } else if (Array.isArray(filter)) {
              value.selected = filter[0]
            } else if (filter) {
              value.selected = filter
            }
          }

          if (value.type === 'custom') {
            value.selected = value.default()
          }
        }
      } else if (editType === 'EDIT') {
        this.alphaModel.dialog.id = { selected: editingRowData.id }
        Object.entries(this.alphaModel.dialog).forEach(([key, value]) => {
          if (Object.keys(editingRowData).includes(key)) {
            if (value.language !== undefined) {
              if (value.language === 'json') {
                value.selected = JSON.stringify(JSON.parse(editingRowData[key]), null, 2)
              } else {
                value.selected = editingRowData[key]
              }
            } else {
              value.selected = editingRowData[key]
            }
          }
        })
        editingRowData = {}
      }
    },
    cancel () {
      Object.keys(this.alphaModel.dialog).forEach(key => {
        const dialog = this.alphaModel.dialog[key]
        if (dialog.selected) {
          if (dialog.type === 'custom') {
            dialog.selected = dialog.default()
          } else {
            dialog.selected = ''
          }
        }
      })
    },
    update (editType) {
      let checkValidity = true
      const dialog = this.alphaModel.dialog
      for (const value of Object.values(dialog)) {
        const isHidden = value.hide
        if (typeof value.selected === 'boolean') {
          if (value.selected === '') {
            this.$notify({
              group: 'alpha',
              type: 'warn',
              title: 'Info',
              duration: 2000,
              text: value.name + ' 항목은 필수입니다.'
            })
            checkValidity = false
          }
        } else {
          if (!isHidden && value.required && !value.selected && value.type !== 'checkbox') {
            this.$notify({
              group: 'alpha',
              type: 'warn',
              title: 'Info',
              duration: 2000,
              text: value.name + ' 항목은 필수입니다.'
            })
            checkValidity = false
          }
        }

        // const isHidden = value.hide && value.hide(editType)
        // if (value.type === 'custom' && value.checkValidity) {
        //   // check validity function should return warning text for invalid situation, but empty string for valid one
        //   const validityText = value.checkValidity(value.selected)
        //   if (validityText) {
        //     this.$notify({
        //       group: 'alpha',
        //       type: 'warn',
        //       title: 'Info',
        //       duration: 2000,
        //       text: validityText
        //     })
        //     checkValidity = false
        //   }
        // } else if (!isHidden && value.required && !value.selected && value.type !== 'checkbox') {
        //   this.$notify({
        //     group: 'alpha',
        //     type: 'warn',
        //     title: 'Info',
        //     duration: 2000,
        //     text: value.name + ' is required'
        //   })
        //   checkValidity = false
        // }
      }

      if (checkValidity === true) {
        const isCreate = () => {
          if (editType === 'CREATE') {
            return true
          } else {
            return false
          }
        }

        if (this.alphaModel.overrideUpdate) {
          this.alphaModel.overrideUpdate()
          return
        }

        const params = isCreate() ? 'createParams' : 'updateParams'
        const action = isCreate() ? 'create' : 'update'
        this.alphaModel[params] = { query: {} }

        if (this.alphaModel.injectedQuery) {
          this.alphaModel[params].query.injectedQuery = this.alphaModel.injectedQuery
        }

        for (const [key, value] of Object.entries(this.alphaModel.dialog)) {
          this.alphaModel[params].query[key] = value.selected
        }

        this.alphaModel.function(action, this.alphaModel[params].query).then(response => {
          if (response.success === true) {
            this.updateSuccess = true
            if (response.msg === null) {
              this.$notify({
                group: 'alpha',
                type: 'success',
                title: 'Info',
                duration: 2000,
                text:
                  this.alphaModel.name +
                  ' 가 ' +
                  (isCreate() ? '생성 되었습니다.' : '업데이트 되었습니다.')
              })
            }
            this.cancel()
          } else {
            this.updateSuccess = false
            if (response.msg === null) {
              this.$notify({
                group: 'alpha',
                type: 'error',
                title: 'Error',
                duration: 2000,
                text:
                  this.alphaModel.name +
                  (isCreate() ? ' 생성을 실패하였습니다.' : ' 업데이트를 실패하였습니다.')
              })
            }
          }
        }).then(() => {
          if (this.updateSuccess === true) {
            this.$alphaDataTableDialogWrapperPlugIn.cancel()
            this.$refs.dataTable.requestTableData(this.alphaModel)
            for (const key in this.alphaModel.dialog) {
              const dialog = this.alphaModel.dialog[key]
              if (dialog.selected) {
                if (dialog.type === 'custom') {
                  dialog.selected = dialog.default()
                } else {
                  dialog.selected = ''
                }
              }
            }
          }
        })
      }

      if (this.alphaModel.onUpdate) {
        this.alphaModel.onUpdate(editType)
      }
    }
  },
  created () {
    this.alphaModel.status = {
      editType: null
    }
  }
}
</script>
