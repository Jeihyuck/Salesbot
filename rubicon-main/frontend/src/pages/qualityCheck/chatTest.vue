<template class="mr-n2">
  <v-col cols="12"  style="height: calc(100vh - 72px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel" ref="chatTestTable">
      
      <template v-slot:tested_custom="{ item }">
        <div> {{ item.tested? 'Y':'-' }}</div>
      </template>
      <template v-slot:response_custom="{ item }">
        <div class="renderedHtml" v-html="renderHtml(item.response)"></div>
      </template>
      <template v-slot:table-buttons="{ }">
        <v-dialog max-width="600" v-model="deleteDialogVisible">
          <template v-slot:activator="{ props: activatorProps }">
            <v-btn v-bind="activatorProps" class="mr-2" color="primary" size="small">Delete</v-btn>
          </template>

          <template v-slot:default="{ isActive }">
            <v-card title="Delete">
              <v-card-text class="pb-0">
                <v-radio-group v-model="testMethod">
                  <v-radio label="&nbsp;Delete with selected items" value="items"></v-radio>
                  <v-radio label="&nbsp;Delete with Test ID" value="testId"></v-radio>
                </v-radio-group>
                <v-combobox
                  variant="outlined"
                  :disabled="testMethod !== 'testId'"
                  class="mb-4"
                  density="compact"
                  base-color="grey-darken-1"
                  hide-details
                  label="Test ID"
                  :items="alphaModel.filter.test_id.selector"
                  v-model="selectedTestId"
                ></v-combobox>
              </v-card-text>

              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                  text="Delete"
                  variant="tonal"
                  class="my-2"
                  @click="delete_test()"
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
            <v-btn v-bind="activatorProps" class="mr-2" color="primary" size="small">Test</v-btn>
          </template>

          <template v-slot:default="{ isActive }">
            <v-card title="Test">
              <v-card-text class="pb-0">
                <v-radio-group v-model="testMethod">
                  <v-radio label="&nbsp;Test with selected items" value="items"></v-radio>
                  <v-radio label="&nbsp;Test with Test ID" value="testId"></v-radio>
                </v-radio-group>
                <v-combobox
                  variant="outlined"
                  :disabled="testMethod !== 'testId'"
                  class="mb-4"
                  density="compact"
                  base-color="grey-darken-1"
                  hide-details
                  label="Test ID"
                  :items="alphaModel.filter.test_id.selector"
                  v-model="selectedTestId"
                ></v-combobox>
              </v-card-text>

              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                  text="Test"
                  variant="tonal"
                  class="my-2"
                  @click="test()"
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
      <template v-slot:table_custom_action="{ item }">
        <v-btn class="mr-1" size="x-small" :color="'primary'" @click="itemTest(item.index, item)">T
        <v-tooltip
          activator="parent"
          location="top"
          height="24px"
          class="text-primary"
        >Test</v-tooltip>
      </v-btn>
      <v-btn class="" size="x-small" :color="'primary'" @click="setRefResponse(item.index, item)">R
        <v-tooltip
          activator="parent"
          location="top"
          height="24px"
          class="text-primary"
        >Set Ref. Response</v-tooltip>
      </v-btn>
    </template>
  </alphaDataTableView>
</v-col>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'
import { marked } from 'marked'

const deleteDialogVisible = ref(false)
const dialogVisible = ref(false)
const testMethod = ref('items')
const selectedTestId = ref(null)
const chatTestTable = ref(null)

watch(
  () => dialogVisible,
  (newVal, oldVal) => {
    if (newVal === true) {
      rubiconAdmin.chatTest.table('list_test_id').then((response)=> {
        alphaModel.filter.test_id.selector = response.data
      })
    }
  }
);


const alphaModel = reactive({
  tableUniqueID: 'chatTest',
  itemName: 'Chat Test',
  paging: { page: 1, itemsPerPage: 100 },
  function: rubiconAdmin.chatTest.table,
  crud: [false, true, false, true],
  headerId: '0f69d1ab-0924-4da1-8532-4a82b4c69fb5',
  customFields: ['tested', 'response'],
  showSelect: true,
  excel: {
    download: {
      fuctionUrl: 'api/rubicon_admin/chat_test/',
      action: 'read_chat_test',
      template: 'chatTestResult',
      filename: 'chatTestResult.xlsx'
    }
  },
  filter: {
    hideBoarder: false,
    tested: {
      label: 'Tested',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      col: 2,
      level: 2
    },
    down: {
      label: 'Down',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      col: 2,
      level: 2
    },
    case: {
      label: 'Case',
      type: 'dropdown',
      clearable: true,
      selector: [],
      col: 3,
      level: 2,
      selected: null
    },
    test_id: {
      label: 'Test ID',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      col: 3,
      level: 2
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
    language: {
      label: 'Language',
      type: 'dropdown',
      clearable: true,
      selector: ['EN', 'KO'],
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
  }
})

function setRefResponse(index, item) {
  console.log(item)
}


function test() {
  const query = {
    testMethod: testMethod.value,
    selected: alphaModel.selected,
    selectedTestId: selectedTestId.value,
  }
  
  if (testMethod.value === 'items') {
    query.selected = alphaModel.selected
    for (let i = 0; i < alphaModel.tableData.length; i++) {
      if (alphaModel.selected.includes(alphaModel.tableData[i].id)) {
        alphaModel.tableData[i].response = ''
      }
    }
  } else {
    for (let i = 0; i < alphaModel.tableData.length; i++) {
      if (selectedTestId.value === alphaModel.tableData[i].test_id) {
        alphaModel.tableData[i].response = ''
      }
    }
  }

  rubiconAdmin.chatTest.table('chat_test', query).then((response)=> {
    cancel()
    chatTestTable.value.search()
  })
}

function itemTest(index, item) {
  const query = {
    testMethod: 'items',
    selected: [item.id]
  }
  
  rubiconAdmin.chatTest.table('chat_test', query).then((response)=> {
    cancel()
    chatTestTable.value.search()
  })
}

function delete_test() {
  const query = {
    testMethod: testMethod.value,
    selected: alphaModel.selected,
    selectedTestId: selectedTestId.value,
  }
  
  rubiconAdmin.chatTest.table('delete_chat_test', query).then((response)=> {
    cancel()
    chatTestTable.value.search()
  })
}



function cancel() {
  dialogVisible.value = false
  deleteDialogVisible.value = false
  selectedTestId.value = null
}


function renderHtml(text) {
  // console.log(text)
  if (text === undefined || text === null) {
    return ''
  } else {
    return marked(text.replace("```markdown", "").replace("```", ""))
  }
}

onMounted(() => {
  rubiconAdmin.testQuery.table('list_case').then((response)=> {
    alphaModel.filter.case.selector = response.data
  })
  rubiconAdmin.chatTest.table('list_test_id').then((response)=> {
    alphaModel.filter.test_id.selector = response.data
  })
  rubiconAdmin.intelligence.table('list').then((response)=> {
    alphaModel.filter.intelligence.selector = response.data
  })
});

</script>

<style scoped>

:deep(.renderedHtml) {
font-weight: 400;
font-size: 1.0em;
font-family: 'Noto Sans KR', Menlo, Monaco, Consolas, ;
line-height: 150%;
}


:deep(.renderedHtml > table) {
border: 2px #838383 solid !important;
width: 100%;
border-collapse: collapse;
text-align: center; 
/* border-radius: 2%; */
overflow: hidden;
padding: 10px;
margin: 5px;
}

:deep(.renderedHtml > body) {
padding: 0.5em;
background: #f5f5f5 !important;
}

:deep(.renderedHtml > h3) {
padding: 5px 0px 1px 0px;
color: #8292eb;
}
table
:deep(.renderedHtml > table, th, td) {
border: 1px #838383 solid !important;
text-align: center;
padding: 2px;
vertical-align: middle;
}


:deep(.renderedHtml > table > tbody > tr) {
border-top: 1px #838383 solid;
border-bottom: 1px #838383 solid;
}

:deep(.renderedHtml > table > thead > tr > th) {
border-right: 1px #838383 solid;
}

:deep(.renderedHtml > table > tbody > tr > td) {
border-right: 1px #838383 solid;
}

:deep(.renderedHtml > ul) {
padding-left: 15px;
}

:deep(.renderedHtml > ul > li > ul) {
padding-left: 15px;

}

:deep(.renderedHtml > p) {
padding-top: 2px;
}

:deep(strong) {
color: #a1d2fc;
}

:deep(.renderedHtml > ol) {
padding-left: 15px;
}

:deep(.renderedHtml > ol) {
padding-left: 15px;
}

:deep(.renderedHtml > p > img) {
padding: 5px;
max-width: 200px !important; /* Set the maximum width */
height: auto; /* Maintains aspect ratio */
}

:deep(.renderedHtml > ul > li > img) {
padding: 5px;
max-width: 200px !important; /* Set the maximum width */
height: auto; /* Maintains aspect ratio */
}
</style>