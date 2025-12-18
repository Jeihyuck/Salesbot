<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel"></alphaDataTableView>
  </v-col>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'

// Lazy-load the component using dynamic import
// const alphaConfirm = () => import('@/components/alpha/alphaConfirm.vue')

// Define the alphaModel object using reactive to make it reactive in the component
const alphaModel = reactive({
  tableUniqueID: 'managedWord',
  itemName: 'Managed Word',
  paging: { page: 1, itemsPerPage: 15 },
  function: rubiconAdmin.managedWord.table,
  crud: [true, true, true, true],
  headerId: 'f172f0e9-a892-4da6-8102-55e4103393af',
  filter: {
    hideBoarder: false,
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
    module: {
      label: 'Module',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: [],
      selected: null,
      col: 3,
      level: 2
    },
    type: {
      label: 'Type',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: [],
      selected: null,
      col: 3,
      level: 2
    },
    processing: {
      label: 'Processing',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: [],
      selected: null,
      col: 3,
      level: 2
    },
    word: {
      label: 'Embedding Search',
      type: 'text',
      selected: null,
      col: 5
    }
  },
  dialogWidth: '600px',
  dialog: {
    module: {
      label: 'Module',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: [],
      selected: null
    },
    type: {
      label: 'Type',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: [],
      selected: null
    },
    processing: {
      label: 'Processing',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: [],
      selected: null
    },
    word: {
      label: 'Word',
      type: 'text',
      selected: null,
    },
    replace_word: {
      label: 'Replace Word',
      type: 'text',
      selected: null,
    }
  }
})

onMounted(() => {
  rubiconAdmin.managedWord.table('list_module').then((response)=> {
    alphaModel.filter.module.selector = response.data
  })
  rubiconAdmin.managedWord.table('list_type').then((response)=> {
    alphaModel.filter.type.selector = response.data
  })
  rubiconAdmin.managedWord.table('list_processing').then((response)=> {
    alphaModel.filter.processing.selector = response.data
  })
});

</script>
