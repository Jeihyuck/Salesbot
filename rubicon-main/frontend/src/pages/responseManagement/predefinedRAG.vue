<template class="mr-n2">
    <v-col cols="12"  style="height: calc(100vh - 72px); overflow-y: auto;">
      <alphaDataTableView :alphaModel="alphaModel" ref="predefinedRAGTable">
        <template v-slot:active_custom="{ item }">
          <div> {{ item.active? 'Y':'-' }}</div>
        </template>
        <template v-slot:channel_filter_custom="{ item }">
          <codemirror
            v-model="item.channel_filter"
            :style="{ borderRadius: '6px', border: '1px solid #444444' }"
            :autofocus="true"
            :lineWrapping="true"
            :indent-with-tab="true"
            :tab-size="2"
            :extensions="extensions"
          />
        </template>
        <template v-slot:matching_rule_custom="{ item }">
          <codemirror
            v-model="item.matching_rule"
            :style="{ borderRadius: '6px', border: '1px solid #444444' }"
            :autofocus="true"
            :lineWrapping="true"
            :indent-with-tab="true"
            :tab-size="2"
            :extensions="extensions"
          />
        </template>
    </alphaDataTableView>
  </v-col>
</template>
  
<script setup>
import { ref, reactive } from 'vue'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'
import { marked } from 'marked'
import { Codemirror } from 'vue-codemirror'
import { EditorView } from "@codemirror/view"
import { json, jsonParseLinter } from '@codemirror/lang-json'
import { vscodeDark } from '@uiw/codemirror-theme-vscode'
import { linter } from '@codemirror/lint'


const extensions = [json(), vscodeDark, linter(jsonParseLinter()), EditorView.lineWrapping]

const alphaModel = reactive({
  tableUniqueID: 'Predefined',
  itemName: 'Predefined RAG',
  paging: { page: 1, itemsPerPage: 15 },
  function: rubiconAdmin.predefinedRAG.table,
  crud: [true, true, true, true],
  headerId: '9d16c6a6-35b2-4036-ad7a-03974e108e95',
  customFields: ['active', 'channel_filter', 'matching_rule'],
  filter: {
    hideBoarder: false,
    country_code: {
      label: 'Country',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: ['KR', 'GB'],
      selected: null,
      col: 2
    }
  },
  dialogWidth: '1200px',
  dialog: {
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
      multiple: false,
      required: true,
      selector: ['KR', 'GB'],
      selected: null
    },
    site_cd: {
      label: 'Site',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: ['B2C'],
      selected: null
    },
    channel_filter: {
      label: 'Channel Filter',
      type: 'code',
      language: 'json',
      default: JSON.stringify(([]), null, 2),
      selected: ''
    },
    matching_rule: {
      label: 'Matching Rule',
      type: 'code',
      language: 'json',
      default: JSON.stringify(({}), null, 2),
      selected: ''
    },
    contents: {
      label: 'Contents',
      type: 'code',
      language: 'markdown',
      selected: ''
    },
    description: {
      label: 'Description',
      type: 'text',
      required: true,
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
        alphaModel.tableData[indexKey].matching_rule = JSON.stringify(JSON.parse(alphaModel.tableData[indexKey].matching_rule), null, 2)
        alphaModel.tableData[indexKey].channel_filter = JSON.stringify(JSON.parse(alphaModel.tableData[indexKey].channel_filter), null, 2)
        alphaModel.tableData[indexKey].shorten_contents = alphaModel.tableData[indexKey].contents.substring(0, 200) + '...'
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