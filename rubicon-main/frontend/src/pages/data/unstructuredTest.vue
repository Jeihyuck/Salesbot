<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel">
      <template v-slot:chunk_custom="{ item }">
        <div class="renderedHtml" v-html="renderHtml(item.chunk)"></div>
      </template>
    </alphaDataTableView>
  </v-col>
</template>

<script setup>
import { ref } from 'vue'
import { rubiconAdmin } from '@/_services'
import { marked } from 'marked'


// Define the alphaModel object using reactive to make it reactive in the component
const alphaModel = reactive({
  tableUniqueID: 'unstructuredIndex',
  itemName: 'Unstructured Index',
  paging: { page: 1, itemsPerPage: 30 },
  function: rubiconAdmin.unstructuredTest.table,
  crud: [false, true, false, false],
  headerId: '0d90582b-675f-4e54-9409-86feeef8e68a',
  customFields: ['chunk'],
  filter: {
    hideBoarder: false,
    country_code: {
      label: 'Country Code',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      selected: null,
      level: 3,
      col: 3
    },
    ai_search_index: {
      label: 'AI Search Index',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 3,
      col: 6
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
    query: {
      label: 'Query',
      type: 'text',
      selected: '',
      col: 12
    }
  }
})

function renderHtml(text) {
  // console.log(text)
  if (text === undefined) {
    return ''
  } else {
    return marked(text.replace("```markdown", "").replace("```", ""))
  }
}


watch(
  () => alphaModel.filter.country_code.selected,
  (newVal, oldVal) => {
    const query = {
      country_code: newVal
    }
    rubiconAdmin.codeMapping.table('listProductCategoryLv1', query).then((response)=> {
      alphaModel.filter.category_lv1.selector = response.data
    })
    alphaModel.filter.category_lv1.selected = null
    alphaModel.filter.category_lv2.selected = null
    alphaModel.filter.category_lv3.selected = null
    rubiconAdmin.unstructuredIndex.table('listIndex', query).then((response)=> {
      alphaModel.filter.ai_search_index.selector = response.data
    })
  },
  { deep: true }  // Enable deep watching
);

watch(
  () => alphaModel.filter.category_lv1.selected,
  (newVal, oldVal) => {
    const query = {
      product_category_lv1: newVal
    }
    rubiconAdmin.codeMapping.table('listProductCategoryLv2', query).then((response)=> {
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
      product_category_lv2: newVal
    }
    rubiconAdmin.codeMapping.table('listProductCategoryLv3', query).then((response)=> {
      alphaModel.filter.category_lv3.selector = response.data
    })
    alphaModel.filter.category_lv3.selected = null
  },
  { deep: true }  // Enable deep watching
);

function test() {
  const query = {
    index: alphaModel.filter.ai_search_index.selected,
    category_lv1: alphaModel.filter.category_lv1.selected,
    category_lv2: alphaModel.filter.category_lv2.selected,
    category_lv3: alphaModel.filter.category_lv3.selected,
    query: alphaModel.filter.query.selected
  }
  rubiconAdmin.unstructuredTest.table('test', query).then((response)=> {
    console.log(response)
  })
}


onMounted(() => {
  console.log('mounted')
});

</script>


<style scoped>
 
 :deep(.renderedHtml) {
  font-weight: 400;
  font-size: 1.0em;
  font-family: 'Noto Sans KR', Menlo, Monaco, Consolas, ;
  line-height: 150%;
}


:deep(.renderedHtml > table) {
  border: 2px #838383 solid !important;
  width: 100%;
  border-collapse: collapse;
  text-align: center; 
  /* border-radius: 2%; */
  overflow: hidden;
  padding: 10px;
  margin: 5px;
}

:deep(.renderedHtml > body) {
  padding: 0.5em;
  background: #f5f5f5 !important;
}

:deep(.renderedHtml > h3) {
  padding: 5px 0px 1px 0px;
  color: #8292eb;
}
 table
:deep(.renderedHtml > table, th, td) {
  border: 1px #838383 solid !important;
  text-align: center;
  padding: 2px;
  vertical-align: middle;
}


:deep(.renderedHtml > table > tbody > tr) {
  border-top: 1px #838383 solid;
  border-bottom: 1px #838383 solid;
}

:deep(.renderedHtml > table > thead > tr > th) {
  border-right: 1px #838383 solid;
}

:deep(.renderedHtml > table > tbody > tr > td) {
  border-right: 1px #838383 solid;
}

:deep(.renderedHtml > ul) {
  padding-left: 15px;
}

:deep(.renderedHtml > ul > li > ul) {
  padding-left: 15px;

}

:deep(.renderedHtml > p) {
  padding-top: 2px;
}

:deep(strong) {
  color: #a1d2fc;
}

:deep(.renderedHtml > ol) {
  padding-left: 15px;
}

:deep(.renderedHtml > ol) {
  padding-left: 15px;
}

:deep(.renderedHtml > p > img) {
  padding: 5px;
  max-width: 200px; /* Set the maximum width */
  height: auto; /* Maintains aspect ratio */
}
  
</style>