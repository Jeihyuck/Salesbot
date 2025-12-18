<template class="mr-n2">
    <v-col cols="12"  style="height: calc(100vh - 72px); overflow-y: auto;">
      <alphaDataTableView :alphaModel="alphaModel">
        <template v-slot:active_custom="{ item }">
          <div> {{ item.active? 'Y':'-' }}</div>
        </template>
        <template v-slot:managed_only_custom="{ item }">
          <div> {{ item.managed_only? 'Y':'-' }}</div>
        </template>
        <template v-slot:reference_custom="{ item }">
          <div> {{ item.reference? 'Y':'-' }}</div>
        </template>
    </alphaDataTableView>
    <!-- Check Log, Resolve,  -->
  </v-col>
</template>
  
<script setup>
import { ref, reactive } from 'vue'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'
import { marked } from 'marked'
import { Codemirror } from 'vue-codemirror'
import { EditorView } from "@codemirror/view"
import { markdown } from '@codemirror/lang-markdown'
import { vscodeDark } from '@uiw/codemirror-theme-vscode'

const extensions = [markdown(), vscodeDark, EditorView.lineWrapping]

const alphaModel = reactive({
  tableUniqueID: 'ManagedResponse',
  itemName: 'Managed Response',
  paging: { page: 1, itemsPerPage: 15 },
  function: rubiconAdmin.managedResponse.table,
  crud: [true, true, true, true],
  headerId: '7161b444-dbbc-4fa6-975f-561b7c08108c',
  customFields: ["active", "managed_only", "reference"],
  filter: {
    hideBoarder: false,
    active: {
      label: 'Active',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: true,
      level: 2,
      col: 2
    },
    managed_only: {
      label: 'Managed Only',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      level: 2,
      col: 2
    },
    reference: {
      label: 'Reference',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      level: 2,
      col: 2
    },
    country_code: {
      label: 'Country',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      level: 2,
      col: 2,
      selected: null
    },
    site_cd: {
      label: 'Site Code',
      type: 'dropdown',
      clearable: true,
      selector: ['B2C'],
      level: 2,
      col: 2,
      selected: null
    },
    product_search: {
      label: 'Product Search (Like Search)',
      type: 'text',
      selected: null,
      col: 4
    },
    function_search: {
      label: 'Function Search',
      type: 'text',
      selected: null,
      col: 3
    },
    date_search: {
      label: 'Date Search',
      type: 'text',
      selected: null,
      col: 3
    }
  },
  dialogWidth: '1200px',
  dialog: {
    active: {
      label: 'Active',
      type: 'dropdown',
      selector: [
        { title: 'Y', value: true },
        { title: '-', value: false }
      ],
      selected: true
    },
    managed_only: {
      label: 'Managed Only',
      type: 'dropdown',
      selector: [
        { title: 'Y', value: true },
        { title: '-', value: false }
      ],
      selected: false
    },
    reference: {
      label: 'Reference',
      type: 'dropdown',
      selector: [
        { title: 'Y', value: true },
        { title: '-', value: false }
      ],
      selected: false
    },
    country_code: {
      label: 'Country',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      selected: null
    },
    site_cd: {
      label: 'Site Code',
      type: 'dropdown',
      clearable: true,
      selector: ['B2C'],
      selected: null
    },
    product: {
      label: 'Product',
      type: 'text',
      required: true,
      selected: ''
    },
    function: {
      label: 'Function',
      type: 'text',
      required: true,
      selected: ''
    },
    date: {
      label: 'Date',
      type: 'text',
      required: true,
      selected: ''
    },
    managed_response: {
      type: 'code',
      label: 'Response Layout',
      language: 'markdown',
      selected: ''
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
  () => alphaModel.tableData,
  (newVal, oldVal) => {
    if ('tableData' in alphaModel) {
      for (const indexKey in alphaModel.tableData) {
        try {
          alphaModel.tableData[indexKey].predefined_query = JSON.stringify(JSON.parse(alphaModel.tableData[indexKey].predefined_query), null, 2)
        } catch (error) {
          alphaModel.tableData[indexKey].predefined_query = JSON.stringify([alphaModel.tableData[indexKey].predefined_query])
        }
        
      }
    }
  },
  { deep: true }  // Enable deep watching
);

onMounted(() => {
  // rubiconAdmin.intelligence.table('list').then((response)=> {
  //   alphaModel.filter.intelligence.selector = response.data
  // })
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
  max-width: 200px !important; /* Set the maximum width */
  height: auto; /* Maintains aspect ratio */
}

:deep(.renderedHtml > ul > li > img) {
  padding: 5px;
  max-width: 200px !important; /* Set the maximum width */
  height: auto; /* Maintains aspect ratio */
}
</style>