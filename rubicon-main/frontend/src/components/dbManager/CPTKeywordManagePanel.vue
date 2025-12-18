<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel" item-value="id" @delete-row="cptKeywordDelete">
      <template v-slot:cpt_keyword_custom="{ item }">
        <v-text-field
            density="compact"
            base-color="grey-darken-1"
            v-model="item.cpt_keyword"
            variant="outlined"
            hide-details
          >
        </v-text-field>
      </template>
        <template v-slot:table-buttons="{ item }">
          <v-dialog max-width="1200" :key='cptKeywordUpdateDialog' v-model="cptKeywordUpdateDialogVisible">
            <template v-slot:activator="{ props: activatorProps }">
              <v-btn v-bind="activatorProps" variant="tonal" color="default" size="small" class="ml-2"> Update CPT Mapping Keyword</v-btn>
            </template>
            <template v-slot:default="{ isActive }">
              <v-card  title="Update CPT Mapping Keyword" class="pa-4">
                <v-card-text class="pb-0">
                  <v-row class="ml-2 mt-4">각 제품의 CPT Keyword 수정 값을 입력하세요.</v-row>
                  <v-row>
                    <v-col cols="8" class="mt-2">
                      <v-text-field
                        density="compact"
                        base-color="grey-darken-1"
                        label="CPT Keyword"
                        v-model="cptKeyword"
                        variant="outlined"
                        hide-details
                      >
                      </v-text-field>
                    </v-col>
                  </v-row>
                </v-card-text>
                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn
                    text="Create"
                    variant="tonal"
                    class="mr-4 my-4"
                    @click="updCPTKeyword()"
                  ></v-btn>
                  <v-overlay
                    :model-value="creatingReferenceResponse"
                    class="align-center justify-center"
                  >
                    <v-progress-circular
                      color="primary"
                      size="64"
                      indeterminate
                    ></v-progress-circular>
                  </v-overlay>
                  <v-btn
                    text="Cancel"
                    variant="tonal"
                    class="mr-4 my-4"
                    @click="cancel()"
                  ></v-btn>
                </v-card-actions>
              </v-card>
            </template>
          </v-dialog>
          <v-btn variant="tonal" color="default" size="small" class="ml-2" @click="cptKeywordUpdate()">Update on Database</v-btn>
          <v-btn variant="tonal" color="default" size="small" class="ml-2" @click="cptKeywordDelete()">Delete from Database</v-btn>
        </template>
    </alphaDataTableView>
  </v-col>
</template>

<script setup>
import { ref, reactive, getCurrentInstance } from 'vue'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'

const cptKeywordUpdateDialogVisible = ref(false)
const cptKeywordUpdateDialog = ref('1')
const cptKeyword = ref('')
const { proxy } = getCurrentInstance()
const alphaModel = reactive({
  tableUniqueID: 'CPTUpdDelData',
  itemName: 'CPT Update/Delete Data',
  paging: { page: 1, itemsPerPage: 30 },
  function: rubiconAdmin.cptUpdDelData.table,
  crud: [false, true, false, true],
  headerId: '491f4b36-e1e4-453d-9b1e-295f1160e58b',
  showSelect: true,
  customFields: ['cpt_keyword'],
  filter: {
    hideBoarder: true,
    op_type: {
      label: 'Operation Type',
      type: 'dropdown',
      clearable: true,
      selector: ['DEV'],
      selected: null,
      col: 2
    },
    country_code: {
      label: 'Country',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      selected: null,
      col: 2
    },
    channel: {
      label: 'Channel',
      type: 'dropdown',
      clearable: true,
      selector: ['B2C', 'FN'],
      selected: null,
      col: 2
    },
    product: {
      label: 'Product',
      type: 'text',
      selected: null,
      col: 3
    },
    keyword: {
      label: 'CPT Keyword',
      type: 'text',
      selected: null,
      col: 3
    }
  },
})

function updCPTKeyword() {
  if (cptKeyword.value === '') {
    proxy.$snackbar.showSnackbar({
      title: 'Input Error',
      message: 'Please fill in CPT Keyword',
      color: 'warning'
    });
    return
  } else {
    const selectedIds = alphaModel.selected || []
    if (selectedIds.length === 0) {
      proxy.$snackbar.showSnackbar({
        title: 'No Selection',
        message: 'Please select at least one row to update.',
        color: 'warning'
      });
      return
    }
    alphaModel.tableData.forEach(row => {
      if (selectedIds.includes(row.id)) {
        row.cpt_keyword = cptKeyword.value
      }
    })
    cancel()
  }
}

function cptKeywordUpdate() {
  const selectedIds = alphaModel.selected || []
  if (selectedIds.length === 0) {
    proxy.$snackbar.showSnackbar({
      title: 'No Selection',
      message: 'Please select at least one row to update.',
      color: 'warning'
    });
    return
  }
  const selectedRows = alphaModel.tableData.filter(row => selectedIds.includes(row.id))
  const query = {    
    cpt_filter: alphaModel.filter,
    cpt_update: selectedRows
  }
  rubiconAdmin.cptUpdDelData.table('updCPTKeyword', query).then((response)=> {
    console.log('CPT Keyword Update Response:', response )
    if (response && response.success === true) {
      proxy.$snackbar.showSnackbar({
        title: 'Update Success',
        message: 'CPT Keyword updated in DB.',
        color: 'success'
      });
    } else {
      proxy.$snackbar.showSnackbar({
        title: 'Update Failed',
        message: response?.msg?.text || 'Update failed',
        color: 'error'
      });
    }
  })
}

function cptKeywordDelete() {
  const selectedIds = alphaModel.selected || []
  if (selectedIds.length === 0) {
    proxy.$snackbar.showSnackbar({
      title: 'No Selection',
      message: 'Please select at least one row to delete.',
      color: 'warning'
    });
    return
  }
  const selectedRows = alphaModel.tableData.filter(row => selectedIds.includes(row.id))
  const query = {    
    cpt_filter: alphaModel.filter,
    cpt_delete: selectedRows
  }
  rubiconAdmin.cptUpdDelData.table('delCPTKeyword', query).then((response) => {
    console.log('delete response:', response)
    if (response && response.success === true) {
      // ✅ 삭제된 row만 화면에서 제거
      alphaModel.tableData = alphaModel.tableData.filter(row => !selectedIds.includes(row.id))
      // 선택 상태 및 체크박스 초기화
      alphaModel.selected = []
    } else {
      proxy.$snackbar.showSnackbar({
        title: 'Delete Failed',
        message: response?.msg?.text || 'Delete failed',
        color: 'error'
      })
    }
  })
}

function cancel() {
  cptKeywordUpdateDialogVisible.value = false
}

function requestTableData() {  
  alphaModel.tableData = response.data
  alphaModel.selected = []
}

onMounted(() => {

});

</script>
