<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel">
      <template v-slot:extended_info_custom="{ item }">
        <codemirror
          v-model="item.extended_info"
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
  tableUniqueID: 'complementationCodeMappingExtended',
  itemName: 'Complementation Code Mapping Extended',
  paging: { page: 1, itemsPerPage: 30 },
  function: rubiconAdmin.complementationCodeMappingExtended.table,
  crud: [false, true, false, false],
  headerId: '32e8afd9-2f92-4d6d-85b5-b82b8e787af3',
  customFields: ["extended_info"],
  filter: {
    hideBoarder: false,
    country_code: {
      label: 'Country',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      selected: null,
      level: 2,
      col: 2
    },
    category_lv1: {
      label: 'Category Lv. 1',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 2,
      col: 3
    },
    category_lv2: {
      label: 'Category Lv. 2',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 2,
      col: 3
    },
    category_lv3: {
      label: 'Category Lv. 3',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 2,
      col: 3
    },
    active: {
      label: 'Active',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      col: 2
    },
    update_tag: {
      label: 'Update Tag',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      col: 3
    },
    edge: {
      label: 'Edge',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      col: 3
    },
    mapping_code: {
      label: 'Mapping Code',
      type: 'text',
      selected: null,
      col: 4
    }
  },
  dialogWidth: '600px',
  // dialog: {
  //   country_code: {
  //     label: 'Country',
  //     type: 'dropdown',
  //     multiple: false,
  //     required: true,
  //     selector: ['KR', 'GB'],
  //     selected: null
  //   },
  //   type: {
  //     label: 'Type',
  //     type: 'text',
  //     multiple: false,
  //     required: true,
  //     selected: ''
  //   },
  //   expression: {
  //     label: 'Expression',
  //     type: 'text',
  //     multiple: false,
  //     required: true,
  //     selected: ''
  //   },
  //   field: {
  //     label: 'Field',
  //     type: 'text',
  //     multiple: false,
  //     required: true,
  //     selected: ''
  //   },
  //   mapping_code: {
  //     label: 'Mapping Code',
  //     type: 'text',
  //     multiple: false,
  //     required: true,
  //     selected: ''
  //   },
  //   category_lv1: {
  //     label: 'Category Lv. 1',
  //     type: 'text',
  //     multiple: false,
  //     selected: ''
  //   },
  //   category_lv1: {
  //     label: 'Category Lv. 1',
  //     type: 'text',
  //     multiple: false,
  //     selected: ''
  //   },
  //   category_lv2: {
  //     label: 'Category Lv. 2',
  //     type: 'text',
  //     multiple: false,
  //     selected: ''
  //   },
  //   category_lv3: {
  //     label: 'Category Lv. 3',
  //     type: 'text',
  //     multiple: false,
  //     selected: ''
  //   }
  // }
})


watch(
  () => alphaModel.filter.country_code.selected,
  (newVal, oldVal) => {
    const query = {
      country_code: newVal
    }
    rubiconAdmin.complementationCodeMappingExtended.table('listCategoryLv1', query).then((response)=> {
      alphaModel.filter.category_lv1.selector = response.data
    })
    alphaModel.filter.category_lv1.selected = null
    alphaModel.filter.category_lv2.selected = null
    alphaModel.filter.category_lv3.selected = null
  },
  { deep: true }  // Enable deep watching
);

watch(
  () => alphaModel.filter.category_lv1.selected,
  (newVal, oldVal) => {
    const query = {
      country_code: alphaModel.filter.country_code.selected,
      category_lv1: newVal
    }
    rubiconAdmin.complementationCodeMappingExtended.table('listCategoryLv2', query).then((response)=> {
      alphaModel.filter.category_lv2.selector = response.data
    })
    alphaModel.filter.category_lv2.selected = null
    alphaModel.filter.category_lv3.selected = null
  },
  { deep: true }  // Enable deep watching
);


watch(
  () => alphaModel.filter.category_lv2.selected,
  (newVal, oldVal) => {
    const query = {
      country_code: alphaModel.filter.country_code.selected,
      category_lv2: newVal
    }
    rubiconAdmin.complementationCodeMappingExtended.table('listCategoryLv3', query).then((response)=> {
      alphaModel.filter.category_lv3.selector = response.data
    })
    alphaModel.filter.category_lv3.selected = null
  },
  { deep: true }  // Enable deep watching
);

onMounted(() => {
  rubiconAdmin.complementationCodeMappingExtended.table('listEdge').then((response)=> {
    alphaModel.filter.edge.selector = response.data
  })

  rubiconAdmin.complementationCodeMappingExtended.table('listUpdateTag').then((response)=> {
    alphaModel.filter.update_tag.selector = response.data
  })

});

// watch(
//   () => alphaModel.tableData,
//   (newVal, oldVal) => {
//     if ('tableData' in alphaModel) {
//       for (const indexKey in alphaModel.tableData) {
//         alphaModel.tableData[indexKey].extended_info = JSON.stringify(JSON.parse(alphaModel.tableData[indexKey].extended_info), null, 2)
//       }
//     }
//   },
//   { deep: true }  // Enable deep watching
// );
</script>
