<template class="mr-n2">
    <v-col cols="12"  style="height: calc(100vh - 72px); overflow-y: auto;">
      <v-row>
        <alphaFilter
          :alphaModel="alphaModel"
          @search="search"
        />
      </v-row>

      <v-row class="pt-0 px-0" density="dense">
        <v-col cols="12" class="px-0">
          <v-card>
            <v-tabs
              v-model="tab"
              bg-color="primary"
            >
              <v-tab value="one">Debug</v-tab>
              <v-tab value="two">User Log (Mongo DB)</v-tab>
            </v-tabs>

            <v-card-text>
              <v-tabs-window v-model="tab">
                <v-tabs-window-item value="one">
                  <div class="renderedHtml ml-n3 pl-1 pr-3" v-html="timeLogs"></div>
                  <codemirror
                    v-model="debugLog"
                    placeholder="{}"
                    :style="{ borderRadius: '6px', border: '1px solid #444444' }"
                    :autofocus="true"
                    :lineWrapping="true"
                    :indent-with-tab="true"
                    :tab-size="2"
                    :extensions="extensions"
                  />
                </v-tabs-window-item>

                <v-tabs-window-item value="two">
                  <codemirror
                    v-model="userLog"
                    placeholder="{}"
                    :style="{ borderRadius: '6px', border: '1px solid #444444' }"
                    :autofocus="true"
                    :lineWrapping="true"
                    :indent-with-tab="true"
                    :tab-size="2"
                    :extensions="extensions"
                  />
                </v-tabs-window-item>
              </v-tabs-window>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- <v-row v-if="alphaModel.filter.log.selected==='Debug'" class="pt-4 px-0">
        <v-col cols="12" class="text-start px-1">
          <div class="renderedHtml ml-n3 pr-2" v-html="timeLogs"></div>
        </v-col>
      </v-row>
      <v-row class="px-0">
        <v-col cols="12" class="text-start px-0">
          <codemirror
          v-model="messageLog"
          placeholder=""
          :style="{ borderRadius: '6px', border: '1px solid #444444' }"
          :autofocus="true"
          :lineWrapping="true"
          :indent-with-tab="true"
          :tab-size="2"
          :extensions="extensions"
        />
        </v-col>

      </v-row> -->
  </v-col>
</template>
  
<script setup>
import { ref, reactive } from 'vue'
import { rubicon, rubiconAdmin } from '@/_services'

import { marked } from 'marked'
import { Codemirror } from 'vue-codemirror'
import { EditorView } from "@codemirror/view"
import { json, jsonParseLinter } from '@codemirror/lang-json'
import { vscodeDark } from '@uiw/codemirror-theme-vscode'
import { linter } from '@codemirror/lint'

import alphaFilter from '@/components/alpha/alphaFilter.vue'

const alphaModel = reactive({
  tableUniqueID: 'full log check',
  function: rubiconAdmin.appraisalCheck.table,
  filter: {
    hideBoarder: false,
    messageID: {
      label: 'Message ID',
      type: 'text',
      col: 8,
      selector: ['Resolved', 'Unresolved', 'ALL'],
      selected: ''
    },
  }
})

const tab = ref(1)
const timeLogs = ref('')
const debugLog = ref('')
const userLog = ref('')
const extensions = [json(), vscodeDark, linter(jsonParseLinter()), EditorView.lineWrapping]

function renderHtml(text) {
  if (text === null) {
    return ''
  } else {
    return marked(text.replace("```markdown", "").replace("```", ""))
  }
}


function search() {
  const query = {
    message_id: alphaModel.filter.messageID.selected
  }

  rubicon.appraisal.function('get_debug', query).then(response => {
    timeLogs.value = renderHtml(response.data.timing_logs)
    debugLog.value = JSON.stringify(response.data.debug_content, null, 2)  
  })

  rubiconAdmin.appraisalCheck.table('check_log', query).then((response) => {
    userLog.value = JSON.stringify(response.data, null, 2)
  })

}

</script>


<style scoped>
div > prevue  {
  white-space: pre-line !important;
}

.markdown-chat {
    /* color: #ffffff; */
    font-weight: 400;
    font-size: 1.0em;
    font-family: 'Noto Sans KR', Menlo, Monaco, Consolas, ;
}

/* .renderedHtml {
  font-weight: 400;
  font-size: 1.0em;
  font-family: 'Noto Sans KR', Menlo, Monaco, Consolas, ;
  line-height: 200%;
} */


:deep(.renderedHtml > table) {
  border: 2px #838383 solid !important;
  width: 100%;
  border-collapse: collapse;
  /* border-radius: 2%; */
  overflow: hidden;
  padding: 10px;
  margin: 10px;
}

:deep(.renderedHtml > body) {
  padding:1.5em;
  background: #f5f5f5 !important;
}

:deep(.renderedHtml > h3) {
  padding: 10px 0px 2px 0px;
  color: #8292eb;
}

:deep(.renderedHtml table, th, td) {
  border: 1px #838383 solid;

  text-align: center;
  padding: 2px !important;
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
  padding-left: 20px;
}

:deep(.renderedHtml > ul > li > ul) {
  padding-left: 20px;

}

:deep(.renderedHtml > p) {
  padding-top: 8px;
  padding-bottom: 5px;
}

:deep(strong) {
  color: #a1d2fc;
}

:deep(.renderedHtml > ol) {
  padding-left: 20px;
}

:deep(.renderedHtml > ol) {
  padding-left: 20px;
}

:deep(.renderedHtml > ol > li > p > img) {
  padding: 10px;
  max-width: 200px; /* Set the maximum width */
  height: auto; /* Maintains aspect ratio */
}

:deep(.renderedHtml img) {
  padding: 10px;
  max-width: 300px; /* Set the maximum width */
  max-height: 300px; /* Set the maximum width */
  height: auto; /* Maintains aspect ratio */
  width: auto
}


</style>
