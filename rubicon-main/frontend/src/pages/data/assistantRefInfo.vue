<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTableView :alphaModel="alphaModel">
      <template v-slot:related_question_custom="{ item }">
        <div class="renderedHtml py-2" v-html="renderHtml(item.related_question)"></div>
      </template>
      <template v-slot:text_custom="{ item }">
        <div class="renderedHtml py-2" v-html="renderHtml(item.text)"></div>
      </template>
    </alphaDataTableView>
  </v-col>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { marked } from 'marked'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'


// Define the alphaModel object using reactive to make it reactive in the component
const alphaModel = reactive({
  tableUniqueID: 'assistantRefInfo',
  itemName: 'Assistant Ref Info',
  paging: { page: 1, itemsPerPage: 10 },
  function: rubiconAdmin.assistantRefInfo.table,
  crud: [true, true, true, true],
  headerId: 'd9bb2bf0-4dd0-497a-9255-7032026b8e53',
  customFields: ['text', 'related_question'],
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
    country_code: {
      label: 'Country',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      selected: null,
      col: 2
    },
    embeddingSearch: {
      label: 'Embedding Search',
      type: 'text',
      selected: null,
      col: 5
    }
  },
  dialogWidth: '600px',
  dialog: {
    country_code: {
      label: 'Country',
      type: 'dropdown',
      multiple: false,
      required: true,
      selector: ['KR', 'GB'],
      selected: null
    },
    title: {
      label: 'Title',
      type: 'text',
      multiple: false,
      required: true,
      selected: ''
    },
    related_question: {
      label: 'Related Question',
      type: 'code',
      language: 'markdown',
      selected: ''
    },
    text: {
      label: 'Text',
      type: 'code',
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
    return marked(text)
  }
}
onMounted(() => {
  rubiconAdmin.assistantRefInfo.table('listUpdateTag').then((response)=> {
    alphaModel.filter.update_tag.selector = response.data
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