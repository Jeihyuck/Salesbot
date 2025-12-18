<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel">
    </alphaDataTableView>
  </v-col>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'

// Define the alphaModel object using reactive to make it reactive in the component
const alphaModel = reactive({
  tableUniqueID: 'unstructuredIndex',
  itemName: 'Unstructured Index',
  paging: { page: 1, itemsPerPage: 10 },
  function: rubiconAdmin.unstructuredIndex.table,
  crud: [true, true, true, true],
  headerId: 'a19d2e4c-1d49-4e9d-a06e-23c33722f23a',
  filter: {
    hideBoarder: false,
    country_code: {
      label: 'Country',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      selected: null,
      col: 2
    },
    op_type: {
      label: 'OP Type',
      type: 'dropdown',
      clearable: true,
      selector: ['DEV', 'STG', 'PROD', 'TEST'],
      selected: null,
      col: 2
    },
  },
  dialogWidth: '600px',
  dialog: {
    country_code: {
      label: 'Country',
      type: 'dropdown',
      required: true,
      selector: ['KR', 'GB'],
      selected: null
    },
    op_type: {
      label: 'OP Type',
      type: 'dropdown',
      required: true,
      selector: ['DEV', 'STG', 'PROD', 'TEST'],
      selected: null
    },
    name: {
      label: 'Name',
      type: 'text',
      required: true,
      selected: ''
    },
    ai_search_index: {
      label: 'AI Search Index',
      type: 'text',
      required: true,
      selected: ''
    }
  }
})


onMounted(() => {
  console.log('mounted')
});

</script>
