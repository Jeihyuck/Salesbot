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


const alphaModel = reactive({
  tableUniqueID: 'specTableMeta',
  itemName: 'Spec Table Meta',
  paging: { page: 1, itemsPerPage: 15 },
  function: rubiconAdmin.specTableMeta.table,
  crud: [true, true, true, true],
  headerId: 'ac8fdb8f-1504-493d-bb87-ad71255d1660',
  filter: {
    hideBoarder: false,
    country_code: {
      label: 'Country Code',
      type: 'dropdown',
      multiple: false,
      clearable: true,
      level: 2,
      col: 2,
      selector: ['KR', 'GB'],
      selected: ''
    },
    category_lv1: {
      label: 'Category Lv1',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 2,
      col: 3
    },
    category_lv2: {
      label: 'Category Lv2',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 2,
      col: 3
    },
    category_lv3: {
      label: 'Category Lv3',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 2,
      col: 3
    },
    model_code: {
      label: 'Model Code',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      col: 2
    },
    spec_lv1: {
      label: 'Spec Lv1',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      col: 2
    },
    spec_lv2: {
      label: 'Spec Lv2',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      col: 2
    },
    spec_value: {
      label: 'Spec Value',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      col: 3
    },
    
  },
  dialogWidth: '600px',
  dialog: {
    country_code: {
      label: 'Country Code',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: ['KR', 'GB'],
      selected: ''
    },
    category_lv1: {
      label: 'Category Lv1',
      type: 'dropdown',
      required: true,
      selector: [],
      selected: ''
    },
    category_lv2: {
      label: 'Category Lv2',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      col: 2
    },
    category_lv3: {
      label: 'Category Lv3',
      type: 'text',
      multiple: false,
      required: true,
      selected: ''
    },
    model_code: {
      label: 'Model Code',
      type: 'text',
      multiple: false,
      required: true,
      selected: ''
    },
    spec_lv1: {
      label: 'Spec Lv1',
      type: 'text',
      multiple: false,
      required: true,
      selected: ''
    },
    spec_lv2: {
      label: 'Spec Lv2',
      type: 'text',
      multiple: false,
      required: true,
      selected: ''
    },
    spec_value: {
      label: 'Spec Value',
      type: 'text',
      multiple: false,
      required: true,
      selected: ''
    }
  }
})

onMounted(() => {
  rubiconAdmin.intelligence.table('list').then((response)=> {
    console.log(response.data)
    alphaModel.filter.intelligence.selector = response.data
  })
});

</script>
