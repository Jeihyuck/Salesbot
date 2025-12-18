<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel" ref="testQueryTable">
      <template v-slot:table-buttons="{ }">
        <v-btn variant="tonal" class="mr-2" color="primary" size="small" @click="downloadTemplate()">Download Template</v-btn>
        <v-dialog max-width="600" v-model="uploadDialogVisible">
          <template v-slot:activator="{ props: activatorProps }">
            <v-btn variant="tonal" v-bind="activatorProps" class="mr-2" color="primary" size="small">Upload Template </v-btn>
          </template>

          <template v-slot:default="{ isActive }">
            <v-card title="Upload Query Template">
              <v-card-text class="pb-0">
                <v-row class="my-4">
                  <v-text-field
                  class="ml-3"
                  density="compact"
                  base-color="grey-darken-1"
                  label="Upload File"
                  v-model="uploadFileName"
                  variant="outlined"
                  hide-details
                >
                </v-text-field>
                <v-btn class="mx-3 mt-1" color="primary" @click="triggerFileUpload()">Select Upload File</v-btn>
                </v-row>

                <file-upload
                  extensions="xls,xlsx,csv"
                  accept=".xlsx,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                  :multiple="false"
                  v-model="files"
                  @input-file="inputFile"
                  ref="fileUploadRef"
                  style="display: none;">
                </file-upload>
              </v-card-text>

              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                  text="Upload"
                  variant="tonal"
                  class="my-2"
                  @click="uploadQuery()"
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
        <v-dialog max-width="600" v-model="dialogVisible">
          <template v-slot:activator="{ props: activatorProps }">
            <v-btn v-bind="activatorProps" class="mr-2" color="primary" size="small">Create Test Case</v-btn>
          </template>

          <template v-slot:default="{ isActive }">
            <v-card title="Make a test case">
              <v-card-text class="pb-0">
                <v-text-field
                  v-model="testID"
                  label="Enter New Test ID"
                  base-color="grey-darken-1"
                  
                  hide-details
                  class="mb-8"></v-text-field>
                <v-radio-group v-model="selectingMethod">
                  <v-radio label="&nbsp;Make a test case with selected items" value="items"></v-radio>
                  <v-radio label="&nbsp;Make a test case with Case IDs" value="cases"></v-radio>
                </v-radio-group>
                <v-combobox
                  variant="outlined"
                  :disabled="selectingMethod !== 'cases'"
                  class="mb-4"
                  density="compact"
                  base-color="grey-darken-1"
                  hide-details
                  multiple
                  label="Select Case IDs"
                  :items="alphaModel.filter.case.selector"
                  v-model="selectedCaseIds"
                ></v-combobox>
              </v-card-text>

              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                  text="Create Test Case"
                  variant="tonal"
                  class="my-2"
                  @click="createTestCase()"
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
        </template>
    </alphaDataTableView>
  </v-col>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'
import { serviceAlpha } from '@/_services/index'
import FileUpload from 'vue-upload-component';


const files = ref([])
const uploadDialogVisible = ref(false)
const dialogVisible = ref(false)
const testID = ref('')
const selectingMethod = ref('items')
const selectedCaseIds = ref([])
const fileUploadRef = ref(null)
const uploadFileName = ref('')
const testQueryTable = ref(null)

const alphaModel = reactive({
  tableUniqueID: 'testQuery',
  itemName: 'Test Query',
  paging: { page: 1, itemsPerPage: 30 },
  function: rubiconAdmin.testQuery.table,
  crud: [true, true, true, true],
  headerId: '9edfc053-1e17-4065-8eb5-ad6edce22f8f',
  dialogWidth: '600px',
  excel: {
    download: {
      fuctionUrl: 'api/rubicon_admin/test_query/',
      action: 'read_test_query',
      template: 'testQueryList',
      filename: 'testQueryList.xlsx'
    }
  },
  showSelect: true,
  filter: {
    hideBoarder: false,
    case: {
      label: 'Case',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      col: 3
    },
    language: {
      label: 'Language',
      type: 'dropdown',
      clearable: true,
      selector: ['EN', 'KO'],
      selected: null,
      col: 2
    },
    channel: {
      label: 'Channel',
      type: 'dropdown',
      clearable: true,
      selector: ['UT-Test-20241112', 'DEV Test', 'DEV Debug'],
      selected: null,
      col: 2
    },
    country: {
      label: 'Country',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      selected: null,
      col: 2
    },
    intelligence: {
      label: 'Intelligence',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      col: 3
    }
  },
  dialog: {
    case: {
      label: 'Case',
      type: 'text',
      required: true,
      selected: ''
    },
    language: {
      label: 'Language',
      type: 'dropdown',
      selector: ['EN', 'KO'],
      selected: ''
    },
    channel: {
      label: 'Channel',
      type: 'dropdown',
      selector: ['UT-Test-20241112', 'DEV Test', 'DEV Debug'],
      selected: null
    },
    country: {
      label: 'Country',
      type: 'dropdown',
      selector: ['KR', 'GB'],
      selected: null
    },
    intelligence: {
      label: 'Intelligence',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: ''
    },
    query: {
      label: 'Query',
      type: 'textarea',
      required: true,
      selected: ''
    },
  }
})

function cancel() {
  uploadDialogVisible.value = false
  dialogVisible.value = false
  files.value = []
  uploadFileName.value = ''
  testID.value = ''
  selectingMethod.value = 'items'
  selectedCaseIds.value = []
}

function downloadTemplate() {
  const fileName = 'uploadQueryTemplate.xlsx'
  serviceAlpha.getFile(fileName, 'uploadQueryTemplate.xlsx')
}

function uploadQuery() {
  serviceAlpha.stdPostFunction(
    'api/rubicon_admin/test_query/',
    {
      action: 'upload_query_template',
      files: files.value
    }
  ).then((response) => {
    console.log(response)
    testQueryTable.value.search()
    cancel()
  })
}


function inputFile(newFile, oldFile) {
  if (newFile && !oldFile) {
    uploadFileName.value = newFile.file.name
  }
}

function triggerFileUpload() {
  if (fileUploadRef.value) {
    const fileInput = fileUploadRef.value.$el.querySelector('input[type="file"]')
    if (fileInput) {
      fileInput.click()
    } else {
      console.error('File input element not found')
    }
  } else {
    console.error('File upload reference not found')
  }
}

function createTestCase() {

  // console.log(alphaModel.selected)
  const query = {
    testID: testID.value,
    selectingMethod: selectingMethod.value,
    selected: alphaModel.selected,
    selectedCaseIds: selectedCaseIds.value,
  }
  rubiconAdmin.testQuery.table('create_test_case', query).then((response)=> {
    cancel()
  })
}

onMounted(() => {
  rubiconAdmin.intelligence.table('list').then((response)=> {
    alphaModel.filter.intelligence.selector = response.data
    alphaModel.dialog.intelligence.selector = response.data
  })
  rubiconAdmin.testQuery.table('list_case').then((response)=> {
    alphaModel.filter.case.selector = response.data
  })
});
</script>
