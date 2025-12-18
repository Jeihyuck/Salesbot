<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel">
      <template v-slot:ner_custom="{ item }">
        <div>{{ item.ner ? 'O' : '' }}</div>
      </template>
      <template v-slot:assistant_custom="{ item }">
        <div>{{ item.assistant ? 'O' : ''}}</div>
      </template>
    </alphaDataTableView>
  </v-col>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'


// Define the alphaModel object using reactive to make it reactive in the component
const alphaModel = reactive({
  tableUniqueID: 'complementDbSearch',
  itemName: 'Complement DB Search',
  paging: { page: 1, itemsPerPage: 10 },
  function: rubiconAdmin.complementDbSearch.table,
  crud: [false, true, false, false],
  headerId: '20de7b85-6c14-4682-a847-561f000e2eee', //7e123b5e-8a16-4ba0-8e60-29a2f03bc251
  customFields: ['ner', 'assistant'],
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
    model_code: {
      label: 'Model Code',
      type: 'text',
      selected: null,
      level: 2,
      col: 3
    },
    embeddingSearch: {
      label: 'Product Expression',
      type: 'text',
      selected: null,
      level: 2,
      col: 3
    },
    table: {
      label: 'Table Name',
      type: 'dropdown',
      clearable: true,
      selector: ['rubicon_data_product_category', 'rubicon_data_product_filter', 'rubicon_data_product_recommend', 'rubicon_v3_complement_product_spec', 'rubicon_data_uk_product_spec_basics', 'rubicon_data_uk_product_filter', 'rubicon_data_uk_product_order'],
      selected: null,
      level: 2,
      col: 5
    },
    spec: {
      label: 'Product Spec',
      type: 'text',
      selected: null,
      col: 4
    },
    color: {
      label: 'Product Color',
      type: 'text',
      selected: null,
      col: 3
    },
    option: {
      label: 'Product Option',
      type: 'text',
      selected: null,
      col: 4
    },
  },
  // dialogWidth: '600px',
  // dialog: {
  //   country_code: {
  //     label: 'Country',
  //     type: 'dropdown',
  //     multiple: false,
  //     required: true,
  //     selector: ['KR', 'GB'],
  //     selected: null
  //   },
  //   // expression: {
  //   //   label: 'Expression',
  //   //   type: 'text',
  //   //   multiple: false,
  //   //   required: true,
  //   //   selected: ''
  //   // },
  //   // mapping_code: {
  //   //   label: 'Mapping Code',
  //   //   type: 'text',
  //   //   multiple: false,
  //   //   required: true,
  //   //   selected: ''
  //   // },
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
    rubiconAdmin.complementationCodeMapping.table('listProductCategoryLv1', query).then((response)=> {
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
      category_lv1: newVal
    }
    rubiconAdmin.complementationCodeMapping.table('listProductCategoryLv2', query).then((response)=> {
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
      category_lv2: newVal
    }
    rubiconAdmin.complementationCodeMapping.table('listProductCategoryLv3', query).then((response)=> {
      alphaModel.filter.category_lv3.selector = response.data
    })
    alphaModel.filter.category_lv3.selected = null
  },
  { deep: true }  // Enable deep watching
);

// onMounted(() => {
//   rubiconAdmin.complementationCodeMapping.table('listField').then((response)=> {
//     alphaModel.filter.field.selector = response.data
//   })

//   rubiconAdmin.complementationCodeMapping.table('listUpdateTag').then((response)=> {
//     alphaModel.filter.update_tag.selector = response.data
//   })

// });

</script>
