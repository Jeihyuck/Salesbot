<template class="mr-n2">
  <v-col cols="12"  style="height: calc(100vh - 72px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel">
    </alphaDataTableView>
  </v-col>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'
import { marked } from 'marked'
import { Codemirror } from 'vue-codemirror'
import { EditorView } from "@codemirror/view"
import { json, jsonParseLinter } from '@codemirror/lang-json'
import { vscodeDark } from '@uiw/codemirror-theme-vscode'
import { linter } from '@codemirror/lint'
import { alphaAuth } from '@/_services'

const alphaModel = reactive({
tableUniqueID: 'appraisalCheck',
itemName: 'Appraisal Check',
paging: { page: 1, itemsPerPage: 15 },
function: rubiconAdmin.appraisalCheck.table,
crud: [false, true, false, false],
headerId: 'cc06df00-47f3-48a9-8e3c-768c3710c52c',
customFields: ['response', 'thumb_up', 'accuracy', 'relevancy', 'harm', 'slow', 'readable', 'else'],
excel: {
  download: {
    fuctionUrl: 'api/rubicon_admin/appraisal_check/',
    action: 'read',
    template: 'appraisalCheck',
    filename: 'appraisalCheck.xlsx'
  }
},
filter: {
  hideBoarder: false,
  date: {
    label: 'Date',
    type: 'date',
    col: 3,
    selected: null
  },
  channel: {
    label: 'Channel',
    type: 'dropdown',
    clearable: true,
    col: 2,
    // selector: ['UT-Test-20241112', 'UT-Test-20241112_KR', 'UT-Test-20241112_UK', 'DEV Test',  'DEV Test_KR',  'DEV Test_UK', 'DEV Debug', 'DEV Debug_KR', 'DEV Debug_UK', 'ALL'],
    selector: ['UT-Test-20241112', 'Security Test', 'DEV Test', 'DEV Debug', 'sprinklr', 'ALL'],
    selected: 'ALL'
  },
  department: {
    label: 'Department',
    type: 'dropdown',
    col: 2,
    selector: [],
    selected: 'ALL'
  },
  thumb_up: {
    label: 'Thumb Up',
    type: 'dropdown',
    col: 2,
    selector: [
      { title: 'Thumb Up', value: true },
      { title: 'Thumb Down', value: false },
      { title: 'ALL', value: 'ALL' },
    ],
    selected: { title: 'ALL', value: 'ALL' }
  },
  status: {
    label: 'Status',
    type: 'dropdown',
    col: 2,
    selector: ['Resolved', 'Unresolved', 'ALL'],
    selected: 'ALL'
  },
},
dialogWidth: '800px',
dialog: {
  virtual_view: {
    label: 'Virtual View',
    type: 'text',
    required: true,
    selected: ''
  },
  config_type: {
    label: 'Config Type',
    type: 'dropdown',
    required: true,
    selector: ['field_mappings', 'relationships', 'source_types'],
    selected: ''
  },
  data_source: {
    label: 'Data Source',
    type: 'text',
    required: true,
    selected: ''
  },
  config: {
    type: 'code',
    language: 'json',
    default: JSON.stringify(
    ({}), null, 2),
    selected: ''
  }
}
})

function renderHtml(text) {
// console.log(text)
if (text === undefined) {
  return ''
} else {
  return marked(text.replace("```markdown", "").replace("```", ""))
}
}

const checkLogDialogVisible = ref(false)
const resolveDialogVisible = ref(false)
const resolveId = ref('')
const resolveComment = ref('')
const mongoLog = ref('{}')
// const readonlyExtension = EditorView.editable.of(false)
// const extensions = [json(), vscodeDark, linter(jsonParseLinter()), EditorView.lineWrapping, readonlyExtension]
const initResolveDialog = (item) => {
// console.log(item)
resolveId.value = item.id
resolveComment.value = ''
}
const getExtensions = () => {
return [json(), vscodeDark, linter(jsonParseLinter()), EditorView.lineWrapping]
}

function thumbUpLabel(thumb_up) {
// console.log(thumb_up)
if (thumb_up === true) {
  return 'Up'
} else if (thumb_up === false) {
  return 'Down'
} else {
  return ''
}
}

function checkLabel(status) {
// console.log(status)
if (status === true) {
  return 'O'
} else {
  return ''
}
}

const appraisalCheckTable = ref(null)

function resolve() {
// console.log('send resolve')
// console.log(resolveId)
// console.log(resolveComment.value)
const query = {
  id: resolveId.value,
  comment: resolveComment.value
}
rubiconAdmin.appraisalCheck.table('resolve', query).then((response)=> {
  // console.log(response.data)
  resolveDialogVisible.value = false
  appraisalCheckTable.value.search()
})
}

function cancel() {
resolveDialogVisible.value = false
checkLogDialogVisible.value = false
}

// const logContent = ref(null);
const logDialog = ref(0);
const checkLog = (index, item) => {
// logDialog.value = logDialog.value + 1
// console.log('checkLog')
const query = {
  id: item.id
}

rubiconAdmin.appraisalCheck.table('check_log', query).then((response)=> {
  mongoLog.value = JSON.stringify(response.data, null, 2)
})

}

watch(
() => alphaModel.tableData,
(newVal, oldVal) => {
  if ('tableData' in alphaModel) {
    for (const indexKey in alphaModel.tableData) {
      try {
        alphaModel.tableData[indexKey].config = JSON.stringify(JSON.parse(alphaModel.tableData[indexKey].config), null, 2)
      } catch (error) {
        alphaModel.tableData[indexKey].config = JSON.stringify([alphaModel.tableData[indexKey].config])
      }
      
    }
  }
},
{ deep: true }  // Enable deep watching
);

onMounted(() => {
alphaAuth.meta.department('listDepartment').then((response)=> {
  // console.log(response.data)
  alphaModel.filter.department.selector = response.data
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
max-width: 200px; /* Set the maximum width */
height: auto; /* Maintains aspect ratio */
}

</style>