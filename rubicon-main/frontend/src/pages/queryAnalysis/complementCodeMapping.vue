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
  tableUniqueID: 'complementationCodeMapping',
  itemName: 'Complementation Code Mapping',
  paging: { page: 1, itemsPerPage: 10 },
  function: rubiconAdmin.complementationCodeMapping.table,
  crud: [true, true, true, true],
  headerId: '65afd359-93c7-418f-9cf5-fc8c487d6c76',
  customFields: ['ner', 'assistant'],
  filter: {
    hideBoarder: false,
    active: {
      label: 'Active',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      level: 3,
      col: 2
    },
    update_tag: {
      label: 'Update Tag',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 3,
      col: 3
    },
    country_code: {
      label: 'Country',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
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
      col: 3
    },
    type: {
      label: 'Type',
      type: 'dropdown',
      clearable: true,
      selector: [],
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
      col: 6
    }
  },
  dialogWidth: '600px',
  dialog: {
    active: {
      label: 'Active',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: [true, false],
      selected: null
    },
    country_code: {
      label: 'Country',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: ['KR', 'GB'],
      selected: null
    },
    type: {
      label: 'Type',
      type: 'text',
      multiple: false,
      required: true,
      selected: ''
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
    category_lv1: {
      label: 'Category Lv. 1',
      type: 'text',
      multiple: false,
      selected: ''
    },
    category_lv1: {
      label: 'Category Lv. 1',
      type: 'text',
      multiple: false,
      selected: ''
    },
    category_lv2: {
      label: 'Category Lv. 2',
      type: 'text',
      multiple: false,
      selected: ''
    },
    category_lv3: {
      label: 'Category Lv. 3',
      type: 'text',
      multiple: false,
      selected: ''
    }
  }
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

onMounted(() => {
  rubiconAdmin.complementationCodeMapping.table('listField').then((response)=> {
    alphaModel.filter.field.selector = response.data
  })

  rubiconAdmin.complementationCodeMapping.table('listUpdateTag').then((response)=> {
    alphaModel.filter.update_tag.selector = response.data
  })

  rubiconAdmin.complementationCodeMapping.table('listType').then((response)=> {
    alphaModel.filter.type.selector = response.data
  })

});

</script>
