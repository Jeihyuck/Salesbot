<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel">
      <template v-slot:active_custom="{ item }">
        <div> {{ item.active? 'Y':'-' }}</div>
      </template>
      <template v-slot:code_filter_custom="{ item }">
        <div> {{ item.code_filter? 'Y':'-' }}</div>
      </template>
      <template v-slot:product_filter_custom="{ item }">
        <div> {{ item.product_filter? 'Y':'-' }}</div>
      </template>
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
  tableUniqueID: 'complementationCodeMappingL4',
  itemName: 'Complementation Code Mapping L4',
  paging: { page: 1, itemsPerPage: 30 },
  function: rubiconAdmin.complementationCodeMappingL4.table,
  crud: [true, true, true, true],
  headerId: '2c33dc4a-36e9-4b89-896c-5de9c71796d7',
  customFields: ["extended_info", "active", "code_filter", "product_filter"],
  filter: {
    hideBoarder: false,
    country_code: {
      label: 'Country',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      selected: null,
      level: 3,
      col: 2
    },
    category_lv1: {
      label: 'Category Lv. 1',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 3,
      col: 3
    },
    category_lv2: {
      label: 'Category Lv. 2',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 3,
      col: 3
    },
    category_lv3: {
      label: 'Category Lv. 3',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 3,
      col: 3
    },
    active: {
      label: 'Active',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      level: 2,
      col: 2
    },
    type: {
      label: 'Type',
      type: 'dropdown',
      clearable: true,
      selector: ['str', 'int'],
      selected: null,
      level: 2,
      col: 2
    },
    condition: {
      label: 'Condition',
      clearable: true,
      type: 'dropdown',
      selector: ['positive', 'negative'],
      selected: null,
      level: 2,
      col: 2
    },
    code_filter: {
      label: 'Code Filter',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      level: 2,
      col: 2
    },
    product_filter: {
      label: 'Product Filter',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      level: 2,
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
    l4_identifier: {
      label: 'L4 Identifier',
      type: 'text',
      selected: null,
      col: 3
    },
    l4_product_expression: {
      label: 'L4 Product Name',
      type: 'text',
      selected: null,
      col: 3
    }
  },
  dialogWidth: '600px',
  dialog: {
    active: {
      label: 'Active',
      type: 'dropdown',
      selector: [true, false],
      selected: true,
    },
    country_code: {
      label: 'Country',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      selected: null,
    },
    category_lv1: {
      label: 'Category Lv. 1',
      type: 'text',
      selected: ''
    },
    category_lv2: {
      label: 'Category Lv. 2',
      type: 'text',
      selected: ''
    },
    category_lv3: {
      label: 'Category Lv. 3',
      type: 'text',
      selected: ''
    },
    type: {
      label: 'Type',
      type: 'dropdown',
      selector: ['str', 'int'],
      selected: null,
    },
    condition: {
      label: 'Condition',
      type: 'dropdown',
      selector: ['positive', 'negative'],
      selected: null,
    },
    l4_identifier: {
      label: 'L4 Identifier',
      type: 'text',
      selected: ''
    },
    l4_product_expression: {
      label: 'L4 Product Expression',
      type: 'text',
      selected: ''
    },
    code_filter: {
      label: 'Code Filter',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      col: 2
    },
    product_filter: {
      label: 'Product Filter',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      col: 2
    }
  }
})


watch(
  () => alphaModel.filter.country_code.selected,
  (newVal, oldVal) => {
    const query = {
      country_code: newVal
    }
    rubiconAdmin.complementationCodeMappingL4.table('listCategoryLv1', query).then((response)=> {
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
    rubiconAdmin.complementationCodeMappingL4.table('listCategoryLv2', query).then((response)=> {
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
    rubiconAdmin.complementationCodeMappingL4.table('listCategoryLv3', query).then((response)=> {
      alphaModel.filter.category_lv3.selector = response.data
    })
    alphaModel.filter.category_lv3.selected = null
  },
  { deep: true }  // Enable deep watching
);

onMounted(() => {
  rubiconAdmin.complementationCodeMappingL4.table('listEdge').then((response)=> {
    alphaModel.filter.edge.selector = response.data
  })

  rubiconAdmin.complementationCodeMappingL4.table('listUpdateTag').then((response)=> {
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
