<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel">
      <template v-slot:base_custom="{ item }">
        <div> {{ item.base? 'Y':'-' }}</div>
      </template>
      <template v-slot:product_card_custom="{ item }">
        <div> {{ item.product_card? 'Y':'-' }}</div>
      </template>
      <template v-slot:related_query_custom="{ item }">
        <div> {{ item.related_query? 'Y':'-' }}</div>
      </template>
      <template v-slot:hyperlink_custom="{ item }">
        <div> {{ item.hyperlink? 'Y':'-' }}</div>
      </template>
      <template v-slot:media_custom="{ item }">
        <div> {{ item.media? 'Y':'-' }}</div>
      </template>
      <template v-slot:map_custom="{ item }">
        <div> {{ item.map? 'Y':'-' }}</div>
      </template>
      <template v-slot:intelligence_meta_custom="{ item }">
        <codemirror
          v-model="item.intelligence_meta"
          :style="{ borderRadius: '6px', border: '1px solid #444444' }"
          :autofocus="true"
          :lineWrapping="true"
          :indent-with-tab="true"
          :tab-size="2"
          :extensions="extensions"
        />
      </template>
      <template v-slot:channel_custom="{ item }">
        <codemirror
          v-model="item.channel"
          :style="{ borderRadius: '6px', border: '1px solid #444444' }"
          :autofocus="true"
          :lineWrapping="true"
          :indent-with-tab="true"
          :tab-size="2"
          :extensions="extensions"
        />
      </template>
    </alphaDataTableView>
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
  tableUniqueID: 'intelligence',
  itemName: 'Intelligence',
  paging: { page: 1, itemsPerPage: 30 },
  function: rubiconAdmin.intelligence.table,
  crud: [true, true, true, true],
  headerId: 'f1564016-4513-4a0c-b3d6-18d745b025bb',
  customFields: ["intelligence_meta", "channel", "base", "product_card", "related_query", "hyperlink", "media", "map"],
  filter: {
    hideBoarder: false,
    intelligence: {
      label: 'Intelligence',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 2,
      col: 5
    },
    base: {
      label: 'Base',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      col: 2
    },
    product_card: {
      label: 'Product Card',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      col: 2
    },
    related_query: {
      label: 'Related Query',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      col: 2
    },
    hyperlink: {
      label: 'Hyperlink',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      col: 2
    },
    media: {
      label: 'Media',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      col: 2
    },
    map: {
      label: 'Map',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      col: 2
    }
  },
  dialogWidth: '600px',
  dialog: {
    intelligence: {
      label: 'Intelligence',
      type: 'text',
      required: true,
      selected: ''
    },
    sub_intelligence: {
      label: 'Sub Intelligence',
      type: 'text',
      required: true,
      selected: ''
    },
    intelligence_desc: {
      label: 'Intelligence Description',
      type: 'text',
      required: true,
      selected: ''
    },
    intelligence_meta: {
      type: 'code',
      language: 'json',
      default: JSON.stringify(([]), null, 2),
      selected: ''
    },
    channel: {
      type: 'code',
      language: 'json',
      default: JSON.stringify(({}), null, 2),
      selected: ''
    },
    base: {
      label: 'Base',
      type: 'dropdown',
      selector: [true, false],
      selected: null,
      default: false
    },
    product_card: {
      label: 'Product Card',
      type: 'dropdown',
      selector: [true, false],
      selected: null,
      default: false
    },
    related_query: {
      label: 'Related Query',
      type: 'dropdown',
      selector: [true, false],
      selected: null,
      default: false
    },
    hyperlink: {
      label: 'Hyperlink',
      type: 'dropdown',
      selector: [true, false],
      selected: null,
      default: false
    },
    media: {
      label: 'Media',
      type: 'dropdown',
      selector: [true, false],
      selected: null,
      default: false
    },
    map: {
      label: 'Map',
      type: 'dropdown',
      selector: [true, false],
      selected: null,
      default: false
    }
  }
})

watch(
  () => alphaModel.tableData,
  (newVal, oldVal) => {
    if ('tableData' in alphaModel) {
      for (const indexKey in alphaModel.tableData) {
        alphaModel.tableData[indexKey].intelligence_meta = JSON.stringify(JSON.parse(alphaModel.tableData[indexKey].intelligence_meta), null, 2)
        alphaModel.tableData[indexKey].channel = JSON.stringify(JSON.parse(alphaModel.tableData[indexKey].channel), null, 2)
      }
    }
  },
  { deep: true }  // Enable deep watching
);


// watch(
//   () => alphaModel.tableData,
//   (newVal, oldVal) => {
//     if ('tableData' in alphaModel) {
//       for (const indexKey in alphaModel.tableData) {
//         alphaModel.tableData[indexKey].intelligence_meta = JSON.stringify(JSON.parse(alphaModel.tableData[indexKey].intelligence_meta), null, 2)
//       }
//     }
//   },
//   { deep: true }  // Enable deep watching
// );


onMounted(() => {
  rubiconAdmin.intelligence.table('listIntelligence').then((response)=> {
    alphaModel.filter.intelligence.selector = response.data
  })

});
</script>
