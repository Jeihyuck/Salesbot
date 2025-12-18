<template>
    <alphaDataTable-view :alphaModel="alphaModel"></alphaDataTable-view>
  </template>
  
  <script setup>
  import { ref, reactive } from 'vue'
  import { rubiconAdmin } from '@/_services'
  import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'
  
  // Lazy-load the component using dynamic import
  // const alphaConfirm = () => import('@/components/alpha/alphaConfirm.vue')
  
  // Define the alphaModel object using reactive to make it reactive in the component
  const alphaModel = reactive({
    tableUniqueID: 'intelligenceT',
    itemName: 'Intelligence',
    paging: { page: 1, itemsPerPage: 15 },
    function: rubiconAdmin.intelligence.table,
    crud: [true, true, true, true],
    headerId: 'f1564016-4513-4a0c-b3d6-18d745b025bb',
    dialogWidth: '600px',
    dialog: {
      intelligence: {
        label: 'Intelligence',
        type: 'text',
        required: true,
        selected: ''
      },
      intelligence_desc: {
        label: 'Description',
        type: 'textarea',
        required: true,
        selected: ''
      },
    }
  })
  </script>
  