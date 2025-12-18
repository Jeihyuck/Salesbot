<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTable-view @onClickRow="onClickRow" ref="dataTableView" :alphaModel="alphaModel">
        <template v-slot:active_custom="{ item }">
          <div> {{ item.active? 'Y':'-' }}</div>
        </template>
        <template v-slot:channel_filter_custom="{ item }">
          <codemirror
            v-model="item.channel_filter"
            :style="{ borderRadius: '6px', border: '1px solid #444444' }"
            :autofocus="true"
            :lineWrapping="true"
            :indent-with-tab="true"
            :tab-size="2"
            :extensions="extensions"
          />
        </template>
    </alphaDataTable-view>
  </v-col>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Codemirror } from 'vue-codemirror'
import { EditorView } from "@codemirror/view"
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'
import { markdown } from '@codemirror/lang-markdown'
import { vscodeDark } from '@uiw/codemirror-theme-vscode'
import { json, jsonParseLinter } from '@codemirror/lang-json'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'
import { linter } from '@codemirror/lint'

const extensions = [json(), vscodeDark, linter(jsonParseLinter()), EditorView.lineWrapping]
// const extensions = [markdown(), vscodeDark, EditorView.lineWrapping]

const alphaModel = reactive({
  tableUniqueID: 'promptTemplate',
  itemName: 'Prompt Template',
  paging: { page: 1, itemsPerPage: 15 },
  function: rubiconAdmin.promptTemplate.table,
  crud: [true, true, true, true],
  headerId: '39145c6d-ed17-48e2-a134-e9cafc4c813f',
  customFields: ['active', 'channel_filter'],
  filter: {
    hideBoarder: false,
    active: {
      label: 'Active',
      type: 'dropdown',
      clearable: true,
      multiple: true,
      selector: [
        { title: 'Y', value: true },
        { title: '-', value: false }
      ],
      selected: true,
      level: 2,
      col: 2
    },
    country_code: {
      label: 'Country',
      type: 'dropdown',
      multiple: false,
      selector: ['KR', 'GB'],
      selected: 'KR',
      level: 2,
      col: 2
    },
    response_type: {
      label: 'Response Type',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 2,
      col: 3
    },
    category_lv1: {
      label: 'Category Lv 1',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      col: 4
    },
    category_lv2: {
      label: 'Category Lv 2',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      col: 6
    }
  },
  dialogWidth: '1600px',
  dialog: {
    active: {
      label: 'Active',
      type: 'dropdown',
      selector: [
        { title: 'Y', value: true },
        { title: '-', value: false }
      ],
      selected: true
    },
    country_code: {
      label: 'Country',
      type: 'dropdown',
      selector: ['KR', 'GB'],
      selected: null
    },
    channel: {
      label: 'Channel',
      type: 'text',
      required: true,
      selected: ''
    },

    response_type: {
      label: 'Response Type',
      type: 'text',
      required: true,
      selected: ''
    },
    category_lv1: {
      label: 'Category Lv 1',
      type: 'text',
      required: false,
      selected: ''
    },
    category_lv2: {
      label: 'Category Lv 2',
      type: 'text',
      required: false,
      selected: ''
    },
    tag: {
      label: 'Tag',
      type: 'text',
      required: false,
      selected: ''
    },
    description: {
      label: 'Description',
      type: 'text',
      required: false,
      selected: ''
    },
    channel_filter: {
      label: 'Channel Filter',
      type: 'code',
      language: 'json',
      default: JSON.stringify([], null, 2),
      selected: ''
    },
    prompt: {
      label: 'Prompt',
      type: 'code',
      language: 'markdown',
      selected: ''
    },
  }
})

// State management
const code = ref(``)
const selectedRow = ref(null)
const onClickRow = (row) => {
  // console.log(row.item.prompt)
  code.value = row.item.prompt
  selectedRow.value = row.item.id
}
const dataTableView = ref(null)
const updatePrompt = () => {
  rubiconAdmin.promptTemplate.table('updatePromptTemplate', { id: selectedRow.value, prompt: code.value }).then((response) => {
    console.log(response)
    dataTableView.value.dataTable.requestTableData()
  })
}  

watch(
  () => alphaModel.tableData,
  (newVal, oldVal) => {
    if ('tableData' in alphaModel) {
      for (const indexKey in alphaModel.tableData) {
        alphaModel.tableData[indexKey].channel_filter = JSON.stringify(JSON.parse(alphaModel.tableData[indexKey].channel_filter), null, 2)
      }
    }
  },
  { deep: true }  // Enable deep watching
);


watch(
  () => alphaModel.filter.response_type.selected,
  (newVal, oldVal) => {
    const query = {
      active: alphaModel.filter.active.selected,
      country_code: alphaModel.filter.country_code.selected,
      response_type: newVal
    }

    rubiconAdmin.promptTemplate.table('listCategoryLv1', query).then((response) => {
      alphaModel.filter.category_lv1.selector = response.data
    })
  },
  { deep: true }  // Enable deep watching
);

watch(
  () => alphaModel.filter.category_lv1.selected,
  (newVal, oldVal) => {
    const query = {
      active: alphaModel.filter.active.selected,
      country_code: alphaModel.filter.country_code.selected,
      response_type: alphaModel.filter.response_type.selected,
      category_lv1: newVal
    }

    rubiconAdmin.promptTemplate.table('listCategoryLv2', query).then((response) => {
      alphaModel.filter.category_lv2.selector = response.data
    })
  },
  { deep: true }  // Enable deep watching
);

onMounted(() => {
  const query = {
    active: alphaModel.filter.active.selected,
    country_code: alphaModel.filter.country_code.selected
  }
  rubiconAdmin.promptTemplate.table('listResponseType', query).then((response) => {
    alphaModel.filter.response_type.selector = response.data
  })

});
</script>
