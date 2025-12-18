<template class="mr-n2">
  <v-col cols="12"  style="height: calc(100vh - 72px); overflow-y: auto;">
    <alphaDataTable-view :alphaModel="alphaModel">
    <template v-slot:query_custom="{ item }">
        <v-textarea
          class="d-flex align-stretch text-area-on-table py-2"
          base-color="grey-darken-1"
          v-model="item.query"
          variant="outlined"
          hide-details
          auto-grow
      ></v-textarea>
    </template>
    <template v-slot:ner_code_mapping_custom="{ item }">
      <codemirror
        v-model="item.ner_code_mapping"
        :style="{ borderRadius: '6px', border: '1px solid #444444' }"
        :autofocus="true"
        :lineWrapping="true"
        :indent-with-tab="true"
        :tab-size="2"
        :extensions="extensions"
      />
    </template>
    <template v-slot:pseudo_query_custom="{ item }">
      <codemirror
        v-model="item.pseudo_query"
        :style="{ borderRadius: '6px', border: '1px solid #444444' }"
        :autofocus="true"
        :lineWrapping="true"
        :indent-with-tab="true"
        :tab-size="2"
        :extensions="extensions"
      />
    </template>
    <template v-slot:table_custom_action="{ item }">
      <v-btn class="" size="x-small" :color="'primary'" @click="update(item.index, item)">U
        <v-tooltip
          activator="parent"
          location="top"
          height="24px"
          class="text-primary"
        >Update</v-tooltip>
      </v-btn>
    </template>
    </alphaDataTable-view>
  </v-col>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'
import { Codemirror } from 'vue-codemirror'
import { EditorView } from "@codemirror/view"
import { json, jsonParseLinter } from '@codemirror/lang-json'
import { vscodeDark } from '@uiw/codemirror-theme-vscode'
import { linter } from '@codemirror/lint'


const extensions = [json(), vscodeDark, linter(jsonParseLinter()), EditorView.lineWrapping]

const alphaModel = reactive({
  tableUniqueID: 'pseudo_query',
  itemName: 'Pseudo Query Training Data',
  paging: { page: 1, itemsPerPage: 15 },
  function: rubiconAdmin.pseudoQuery.table,
  crud: [true, true, false, true],
  headerId: '5e4d17bb-ffbd-4069-b42b-64f51bc76d6b',
  customFields: ['query', 'ner_code_mapping', 'pseudo_query'],
  filter: {
    hideBoarder: false,
    country_code: {
      label: 'Country',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: ['KR', 'GB'],
      selected: null,
      col: 2
    },
    embeddingSearch: {
      label: 'Embedding Search',
      type: 'text',
      selected: null,
      col: 8
    }
  },
  dialogWidth: '800px',
  dialog: {
    country_code: {
      label: 'Country',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: ['KR', 'GB'],
      selected: null
    },
    query: {
      label: 'Query',
      type: 'text',
      required: true,
      selected: ''
    },
    ner_code_mapping: {
      type: 'code',
      language: 'json',
      default: JSON.stringify(
      ({
        "measure": [
          {
            "field": "",
            "expression": ""
          }
        ],
        "dimension": [
          {
            "field": "",
            "expression": ""
          }
        ]
      }), null, 2),
      selected: ''
    },
    pseudo_query: {
      type: 'code',
      language: 'json',
      default: JSON.stringify(
      ({
        "measure": [
          {
            "field": "",
            "expression": ""
          }
        ],
        "dimension": [
          {
            "field": "",
            "expression": ""
          }
        ]
      }), null, 2),
      selected: ''
    }
  }
})

const update = (index, item) => {
  // console.log(index)
  // console.log(item)
  // item.measure_dimension = JSON.parse(item.measure_dimension)
  item.confirmed = '-'
  rubiconAdmin.pseudoQuery.table('update', item).then((response)=> {
    console.log(response)
  })
}

watch(
  () => alphaModel.tableData,
  (newVal, oldVal) => {
    if ('tableData' in alphaModel) {
      for (const indexKey in alphaModel.tableData) {
        alphaModel.tableData[indexKey].ner_code_mapping = JSON.stringify(JSON.parse(alphaModel.tableData[indexKey].ner_code_mapping), null, 2)
        alphaModel.tableData[indexKey].pseudo_query = JSON.stringify(JSON.parse(alphaModel.tableData[indexKey].pseudo_query), null, 2)
      }
    }
  },
  { deep: true }  // Enable deep watching
);

</script>

<style>
.text-area-on-table {
  height: 100%;
}

.text-area-on-table > div {
  width: 100% !important;
}

</style>