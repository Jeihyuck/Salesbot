<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel">
      <template v-slot:cpt_keyword_custom="{ item }">
        <v-text-field
          density="compact"
          base-color="grey-darken-1"
          v-model="item.cpt_keyword"
          variant="outlined"
          hide-details
        ></v-text-field>
      </template>
      <template v-slot:table-buttons="{ item }">
        <v-dialog max-width="1200" :key='cptKeywordInputDialog' v-model="cptKeywordInputDialogVisible">
          <template v-slot:activator="{ props: activatorProps }">
            <v-btn v-bind="activatorProps" variant="tonal" color="default" size="small" class="ml-2"> Add CPT Mapping Keyword</v-btn>
          </template>
          <template v-slot:default="{ isActive }">
            <v-card title="Add CPT Mapping Keyword" class="pa-4">
              <v-card-text class="pb-0">
                <v-row class="ml-2 mt-4">각 제품에 맵핑하고자 하는 CPT Keyword 를 입력하세요.</v-row>
                <v-row>
                  <v-col cols="8" class="mt-2">
                    <v-text-field
                      density="compact"
                      base-color="grey-darken-1"
                      label="CPT Keyword"
                      v-model="cptKeyword"
                      variant="outlined"
                      hide-details
                    ></v-text-field>
                  </v-col>
                </v-row>
              </v-card-text>
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                  text="Create"
                  variant="tonal"
                  class="mr-4 my-4"
                  @click="addCPTKeyword()"
                ></v-btn>
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
        <v-btn variant="tonal" color="default" size="small" class="ml-2" @click="cptKeywordInsert()">Insert to Database</v-btn>
      </template>
    </alphaDataTableView>
  </v-col>
</template>

<script setup>
import { ref, reactive, getCurrentInstance } from 'vue'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'

const cptKeywordInputDialogVisible = ref(false)
const cptKeywordInputDialog = ref('1')
const cptKeyword = ref('')
const { proxy } = getCurrentInstance()
const alphaModel = reactive({
  tableUniqueID: 'CPTMappingData',
  itemName: 'CPT Mapping Data',
  paging: { page: 1, itemsPerPage: 30 },
  function: rubiconAdmin.cptMappingData.table,
  crud: [false, true, true, true],
  headerId: '5bafa2bf-d84d-40e9-bd5c-8d02e95269b2',
  customFields: ['cpt_keyword'],
  showSelect: true, // 체크박스 표시
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
    }
  },
})

function addCPTKeyword() {
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
        message: 'Please select at least one row to add.',
        color: 'warning'
      });
      return
    }
    alphaModel.tableData.forEach(row => {
      if (selectedIds.includes(row.id)) {
        row.cpt_keyword = cptKeyword.value
      }
    })
    alphaModel.selected = []
    cancel()
  }
}

function cptKeywordInsert() {
  const query = {
    cpt_filter: alphaModel.filter,
    cpt_mapping: alphaModel.tableData
  }
  rubiconAdmin.cptMappingData.table('addCPTKeyword', query).then((response)=> {
    console.log('CPT Keyword Update Response:', response )
  })
}

function cancel() {
  cptKeywordInputDialogVisible.value = false
}

function requestTableData() {
  // 기존: Product 값 없으면 에러
  // 변경: Product 값 없어도 전체 조회
  const query = { ...alphaModel.filter }
  const paging = {
    page: alphaModel.paging.page,
    itemsPerPage: alphaModel.paging.itemsPerPage
  }
  rubiconAdmin.cptMappingData.table('read', query, paging).then((response) => {
    alphaModel.tableData = response.data
    alphaModel.selected = []
  })
}
</script>
