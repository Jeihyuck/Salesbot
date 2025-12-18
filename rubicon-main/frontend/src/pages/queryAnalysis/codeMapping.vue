<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel">
      <template v-slot:mapping_code_desc_custom="{ item }">
        <div>{{ checkLabel(item.mapping_code_desc) }}</div>
      </template>
    </alphaDataTableView>
  </v-col>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'

// Lazy-load the component using dynamic import
// const alphaConfirm = () => import('@/components/alpha/alphaConfirm.vue')
function checkLabel(status) {
  // console.log(status)
  if (status === true) {
    return 'O'
  } else {
    return ''
  }
}
// Define the alphaModel object using reactive to make it reactive in the component
const alphaModel = reactive({
  tableUniqueID: 'codeMapping',
  itemName: 'Code Mapping',
  paging: { page: 1, itemsPerPage: 10 },
  function: rubiconAdmin.codeMapping.table,
  crud: [true, true, true, true],
  headerId: 'c0937e02-dc5f-47f7-9f15-3abb52176433',
  customFields: ['mapping_code_desc'],
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
    active: {
      label: 'Active',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      level: 3,
      col: 2
    },
    structured: {
      label: 'Structured',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      level: 3,
      col: 2
    },
    field: {
      label: 'Field',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 3,
      col: 2
    },
    expression_to_code: {
      label: 'Expression To Code',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      level: 3,
      col: 2
    },
    expression: {
      label: 'Expression Exact Search',
      type: 'text',
      selected: null,
      col: 5
    },
    embeddingSearch: {
      label: 'Embedding Search',
      type: 'text',
      selected: null,
      col: 5
    }
  },
  dialogWidth: '600px',
  dialog: {
    country_code: {
      label: 'Country',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: ['KR', 'GB'],
      selected: null
    },
    structured: {
      label: 'Structured',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null
    },
    expression: {
      label: 'Expression',
      type: 'text',
      multiple: false,
      required: true,
      selected: ''
    },
    field: {
      label: 'Field',
      type: 'text',
      multiple: false,
      required: true,
      selected: ''
    },
    mapping_code: {
      label: 'Mapping Code',
      type: 'text',
      multiple: false,
      required: true,
      selected: ''
    },
    expression_to_code: {
      label: 'EtoC',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      required: true,
      selected: null
    }
  }
})

onMounted(() => {
  rubiconAdmin.codeMapping.table('listField').then((response)=> {
    alphaModel.filter.field.selector = response.data
  })

});

</script>
