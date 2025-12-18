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
  tableUniqueID: 'productNameInference',
  itemName: 'Managed Word',
  paging: { page: 1, itemsPerPage: 15 },
  function: rubiconAdmin.productNameInference.table,
  crud: [true, true, true, true],
  headerId: '37e37292-6233-412e-b6b6-f2910bed4687',
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
    country_code: {
      label: 'Country',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      selected: null,
      col: 2
    },
    field: {
      label: 'Field',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: ['product_model'],
      selected: null,
      col: 3,
    },
    expression: {
      label: 'Expression',
      type: 'text',
      selected: null,
      col: 4
    }
  },
  dialogWidth: '600px',
  dialog: {
    active: {
      label: 'Active',
      type: 'dropdown',
      required: true,
      clearable: true,
      selector: [true, false],
      selected: null
    },
    country_code: {
      label: 'Country Code',
      type: 'dropdown',
      required: true,
      selector: ['KR', 'GB'],
      selected: null
    },
    field: {
      label: 'Field',
      type: 'dropdown',
      required: true,
      selector: ['product_model'],
      selected: 'product_model'
    },
    expression: {
      label: 'Expression',
      type: 'text',
      selected: null,
    },
    inferred_name: {
      label: 'Inferred Name',
      type: 'text',
      selected: null,
    },
  }
})

onMounted(() => {
  // rubiconAdmin.productNameInference.table('list_module').then((response)=> {
  //   alphaModel.filter.module.selector = response.data
  // })
});

</script>
