<template class="mr-n2">
  <v-col cols="12"  style="height: calc(100vh - 72px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel">
    <template v-slot:measure_dimension_custom="{ item }">
      <codemirror
        v-model="item.measure_dimension"
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
  tableUniqueID: 'ner',
  itemName: 'Ner Training Data',
  paging: { page: 1, itemsPerPage: 15 },
  function: rubiconAdmin.ner.table,
  crud: [true, true, true, true],
  headerId: 'cb742529-3a60-4e8b-998d-e867290d6257',
  customFields: ['measure_dimension'],
  filter: {
    hideBoarder: false,
    active: {
      label: 'active',
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
    // intelligence: {
    //   label: 'Intelligence',
    //   type: 'dropdown',
    //   clearable: true,
    //   multiple: false,
    //   selector: [],
    //   selected: null,
    //   level: 2,
    //   col: 3
    // },
    country_code: {
      label: 'Country',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      selected: null,
      col: 2
    },
    site_cd: {
      label: 'Site',
      type: 'dropdown',
      clearable: true,
      selector: ['B2C'],
      selected: 'B2C',
      col: 2
    },
    // virtual_view: {
    //   label: 'Virtual View',
    //   type: 'dropdown',
    //   clearable: true,
    //   multiple: false,
    //   selector: [],
    //   selected: null,
    //   col: 3
    // },
    embeddingSearch: {
      label: 'Embedding Search',
      type: 'text',
      selected: null,
      col: 4
    }
  },
  dialogWidth: '600px',
  dialog: {
    level: 2,
    active: {
      label: 'active',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null
    },
    query: {
      label: 'Query',
      type: 'text',
      required: true,
      selected: ''
    },
    // intelligence: {
    //   label: 'Intelligence',
    //   type: 'dropdown',
    //   required: true,
    //   selector: [],
    //   selected: null
    // },
    country_code: {
      label: 'Country',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      selected: null,
    },
    site_cd: {
      label: 'Site',
      type: 'dropdown',
      clearable: true,
      selector: ['B2C'],
      selected: 'B2C'
    },
    // virtual_view: {
    //   label: 'Virtual View',
    //   type: 'dropdown',
    //   required: true,
    //   selector: [],
    //   selected: null
    // },
    measure_dimension: {
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
  rubiconAdmin.ner.table('update', item).then((response)=> {
    console.log(response)
  })
}

watch(
  () => alphaModel.tableData,
  (newVal, oldVal) => {
    if ('tableData' in alphaModel) {
      for (const indexKey in alphaModel.tableData) {
        alphaModel.tableData[indexKey].measure_dimension = JSON.stringify(JSON.parse(alphaModel.tableData[indexKey].measure_dimension), null, 2)
      }
    }
  },
  { deep: true }  // Enable deep watching
);

onMounted(() => {
  rubiconAdmin.intelligence.table('list').then((response)=> {
    alphaModel.filter.intelligence.selector = response.data
    alphaModel.dialog.intelligence.selector = response.data
  })
  rubiconAdmin.ner.table('listUpdateTag').then((response)=> {
    alphaModel.filter.update_tag.selector = response.data
  })
  rubiconAdmin.ner.table('listSiteCd').then((response)=> {
    alphaModel.filter.site_cd.selector = response.data
  })
});
</script>

<style>
.text-area-on-table {
  height: 100%;
}

.text-area-on-table > div {
  width: 100% !important;
}

</style>