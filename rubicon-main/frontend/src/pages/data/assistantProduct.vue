<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel">
      <template v-slot:key_features_custom="{ item }">
        <div class="renderedHtml py-2" v-html="renderHtml(item.key_features)"></div>
      </template>
    </alphaDataTableView>
  </v-col>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { marked } from 'marked'
import { rubiconAdmin } from '@/_services'

// import { Codemirror } from 'vue-codemirror'
// import { EditorView } from "@codemirror/view"
// import { json, jsonParseLinter } from '@codemirror/lang-json'
// import { vscodeDark } from '@uiw/codemirror-theme-vscode'
// import { linter } from '@codemirror/lint'

import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'

// const readonlyExtension = EditorView.editable.of(false)
// const extensions = [json(), vscodeDark, linter(jsonParseLinter()), EditorView.lineWrapping, readonlyExtension]

const alphaModel = reactive({
  tableUniqueID: 'assistantProduct',
  itemName: 'Assistant Product',
  paging: { page: 1, itemsPerPage: 15 },
  function: rubiconAdmin.assistantProduct.table,
  crud: [true, true, true, true],
  headerId: 'fee59d17-6a91-4d2b-b198-500ff449585c',
  customFields: ['key_features'],
  filter: {
    hideBoarder: false,
    country_code: {
      label: 'Country Code',
      type: 'dropdown',
      multiple: false,
      col: 2,
      selector: ['KR', 'GB'],
      selected: 'KR'
    },
    category: {
      label: 'Category',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      col: 3
    }
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
    category: {
      label: 'Category',
      type: 'text',
      multiple: false,
      required: true,
      selected: ''
    },
    preferred_recommendation: {
      label: 'Preferred Recommendation',
      type: 'dropdown',
      selector: ['True', 'nan'],
      selected: null,
    },
    product: {
      label: 'Product',
      type: 'text',
      required: true,
      selected: ''
    },
    spec: {
      label: 'Spec',
      type: 'text',
      required: true,
      selected: ''
    },
    key_features: {
      label: 'Features',
      type: 'textarea',
      required: true,
      selected: ''
    },
    target_audience: {
      label: 'Audience',
      type: 'textarea',
      required: true,
      selected: ''
    },
  }
})

function renderHtml(text) {
  // console.log(text)
  if (text === undefined) {
    return ''
  } else {
    return marked(text)
  }
}

watch(
  () => alphaModel.filter.country_code.selected,
  (newVal, oldVal) => {
    const query = {
      country_code: newVal
    }

    rubiconAdmin.assistantProduct.table('listCategory', query).then((response)=> {
      alphaModel.filter.category.selector = response.data
      alphaModel.dialog.category.selector = response.data
    })
  },
  { deep: true }  // Enable deep watching
);

onMounted(() => {
  const query = {
    country_code: alphaModel.filter.country_code.selected,
  }
  rubiconAdmin.assistantProduct.table('listCategory', query).then((response)=> {
    alphaModel.filter.category.selector = response.data
    alphaModel.dialog.category.selector = response.data
  })
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
:deep(.renderedHtml > h2) {
  padding: 5px 0px 1px 0px;
  font-size: 1.4em;
  color: #3d58f0;
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