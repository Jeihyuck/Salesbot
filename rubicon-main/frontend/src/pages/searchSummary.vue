<template>
  <v-row v-if="!envStore.isMobile" class="pt-0" id='chatMainWindow'>
    <v-col cols="3">
      <div class="pl-3 pt-1 pb-1"  style="font-weight: bold;">GPT Model</div>
      <v-select
        class="px-1 pt-0"
        hide-details
        variant="outlined"
        density="compact"
        lable="GPT Model"
        :items="gptModels"
        v-model="selectedLLMModel"
      >
      </v-select>
      <div class="pl-3 pt-1 pb-1"  style="font-weight: bold;">Channel</div>
      <v-select
        class="px-1 pt-0"
        hide-details
        variant="outlined"
        density="compact"
        lable="Channel"
        :items="channels"
        v-model="selectedChannel"
      >
      </v-select>
      <div class="pl-3 pt-1 pb-1"  style="font-weight: bold;">Country</div>
      <v-select
        class="px-1 pt-0"
        hide-details
        variant="outlined"
        density="compact"
        lable="Country"
        :items="countries"
        v-model="selectedCountry"
      >
      </v-select>
      <!-- <div class="pl-3 pt-1 pb-1"  style="font-weight: bold;">Language</div>
      <v-select
        class="px-1 pt-0"
        hide-details
        variant="outlined"
        density="compact"
        lable="Country"
        :items="languages"
        v-model="selectedLanguage"
      >
      </v-select> -->
      <v-text-field
        class="pl-1 pt-4 pr-1"
        variant="outlined"
        density="compact"
        hide-details
        color="primary"
        label="Estore Sitecode"
        v-model="estoreSitecode"
      ></v-text-field>
      <v-text-field
        class="pl-1 pt-2 pr-1"
        variant="outlined"
        density="compact"
        hide-details
        color="primary"
        label="Request SA ID"
        v-model="requestSAID"
      ></v-text-field>
      <v-text-field
        class="pl-1 pt-2 pr-1"
        variant="outlined"
        density="compact"
        hide-details
        color="primary"
        label="Request GUID"
        v-model="requestGUID"
      ></v-text-field>
      <v-text-field
        class="pl-1 pt-2 pr-1"
        variant="outlined"
        density="compact"
        hide-details
        color="primary"
        label="jwtToeken"
        v-model="jwtToken"
      ></v-text-field>
      <v-switch
        class="pl-2 pt-4 mt-n4"
        color="primary"
        v-model="markdown"
        :label="`Markdown: ${markdown ? 'On' : 'Off'}`"
        hide-details
      ></v-switch>
      <v-switch
        class="pl-2 pt-0 mt-n4"
        color="primary"
        v-model="backendCache"
        :label="`Cache: ${backendCache ? 'On' : 'Off'}`"
        hide-details
      ></v-switch>
      <v-switch
        class="pl-2 pt-0 mt-n4"
        color="primary"
        v-model="streaming"
        :label="`Streaming: ${streaming ? 'On' : 'Off'}`"
        hide-details
      ></v-switch>
      <v-switch
        class="pl-2 pt-0 mt-n4"
        color="primary"
        v-model="themeStore.darkMode"
        :label="`Dark Mode: ${darkMode ? 'On' : 'Off'}`"
        hide-details
      ></v-switch>
      <div class="mt-0 mx-1">
        <v-btn block variant="tonal" prepend-icon="mdi-broom" @click="initializeSessionId()">
          <template v-slot:prepend>
            <v-icon color="primary"></v-icon>
          </template>
        &nbsp;New Session</v-btn>
      </div>
    </v-col>
    <v-col cols="9"  class="px-4" id="chatWindow" style="height: calc(100vh - 54px); overflow-y: auto;" :style="getComputedStyle('chatWindow')">
      <v-row class="py-10"></v-row>
      <v-container fluid style="position: fixed; top: 60px; height: calc(100vh - 90px); overflow-y: auto; width: calc(100vw - (100vw / 4)); z-index: 1;">
        <div class="pl-4 ml-4 pr-8 font-weight-medium pb-2"> Rubicon Search Test</div>
        <v-textarea
          auto-grow
          :disabled="chatDisabled"
          class="pl-4 ml-4 pr-12"
          :bg-color="getComputedStyle('queryBox')"
          :label="messageBoxLabel"
          persistent-placeholder
          placeholder="Message (Ctrl+Enter to send)"
          hide-details
          v-model="query"
          rows="1"
          :focused="textareaFocused"
          variant="solo-filled"
          append-icon="mdi-magnify"
          @click:append="fetchResponse()"
        />
        <v-divider class="mx-2 mt-2 mb-2" color="white"></v-divider>
        <v-row>
          <v-col cols="2">
            <v-dialog max-width="1200" :key='productCodeSelect' v-model="productCodeSelectVisible">
                <template v-slot:activator="{ props: activatorProps }">
                  <v-btn v-bind="activatorProps" variant="tonal" color="primary" class="ml-7 mb-2">Select Product</v-btn>
                </template>
                <template v-slot:default="{ isActive }">
                  <v-card  title="Product Select" class="mt-2 pt-4 px-3">
                    <alphaDataTableView class = "px-6" :alphaModel="alphaModel">
                      <template v-slot:table_custom_action="{ item }">
                        <v-btn v-bind="activatorProps" class="mr-1 ml-0" size="x-small" color="primary" @click="addToSelectedProduct(item)">S
                          <v-tooltip
                            activator="parent"
                            location="top"
                            height="24px"
                            class="text-primary"
                            >Add to Selected Product List</v-tooltip>
                        </v-btn>
                    </template>
                    </alphaDataTableView>

                    <v-card-text class="pb-0">
                      <div class="text-caption pl-2 pb-1">Selected Product Codes</div>
                      <codemirror
                        v-model="selectedProductCodes"
                        :style="{ borderRadius: '6px', border: '1px solid #444444' }"
                        :autofocus="true"
                        :lineWrapping="true"
                        :indent-with-tab="true"
                        :tab-size="2"
                        :extensions="extensions"
                      />
                    </v-card-text>

                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn
                        text="Confirm"
                        variant="tonal"
                        class="mr-4 my-4"
                        @click="confirm()"
                      ></v-btn>
                      <v-btn
                        text="Cancel"
                        variant="tonal"
                        class="mr-4 my-4"
                        @click="cancel()"
                      ></v-btn>
                    </v-card-actions>
                  </v-card>
                </template>
              </v-dialog>
          </v-col>
          <v-col cols="9" class="pr-4">
            <codemirror
              v-model="selectedProductCodes"
              :style="{ borderRadius: '6px', border: '1px solid #444444' }"
              :autofocus="true"
              :lineWrapping="true"
              :indent-with-tab="true"
              :tab-size="2"
              :extensions="extensions"
            />
          </v-col>
        </v-row>

        <v-row>
          <search-result
            class="mr-8"
            :content="searchResultContent"
            :model="selectedLLMModel"
            :showMarkdown="markdown"
            :eosDetected="searchResultContentEOS"
            :messageId="currentMessageID"
            :channel="selectedChannel"
            :countryCode="selectedCountry"
              />
        </v-row>
      </v-container>

      <div style="display: none" v-shortkey="['ctrl', 'enter']" @shortkey.propagate="sendMessage"></div>
  </v-col>
  </v-row>
</template>

<script setup>

import FileUpload from 'vue-upload-component';
import 'github-markdown-css';
import { v4 as uuidv4 } from 'uuid';
import { rubicon } from '@/_services'
import { rubiconAdmin } from '@/_services';
import { useAuthStore } from '@/stores/auth';
import { getDatetimeString } from '@/_helpers';
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue';
import { useEnvStore } from '@/stores/env'
import { useThemeStore } from '@/stores/theme'
import { useRouter } from 'vue-router'

import { Codemirror } from 'vue-codemirror'
import { EditorView } from "@codemirror/view"
import { json, jsonParseLinter } from '@codemirror/lang-json'
import { vscodeDark } from '@uiw/codemirror-theme-vscode'
import { linter } from '@codemirror/lint'
import SearchResult from '@/components/chat/SearchResult';

const extensions = [json(), vscodeDark, linter(jsonParseLinter()), EditorView.lineWrapping]

const productCodeSelectVisible = ref(false)
const productCodeSelect = ref('1')


function confirm() {
  productCodeSelectVisible.value = false
}

function cancel() {
  productCodeSelectVisible.value = false
}


const themeStore = useThemeStore()
const envStore = useEnvStore()
const router = useRouter()

const authStore = useAuthStore()
const textareaFocused = ref(false);

// Reactive state variables
const simple = ref(false);
const markdown = ref(false);
const backendCache = ref(false);
const streaming = ref(true);

const chatDisabled = ref(false);
const selectedProductCodes = ref('');




const files = ref([]);
const alphaApiKey = ref('');
const url = ref('');
const formData = ref(new FormData());
const queryReady = ref(false);
const query = ref('');
const sessionId = ref('');
const userId = ref('-');
const estoreSitecode = ref('default_estore_sitecode');
const requestSAID = ref('default_sa_id');
const requestGUID = ref('default_gu_id');
const jwtToken = ref('default_jwt_token');
const tempTime = ref(null);
const countries = ref(['GB', 'KR']);
const channels = ref(['DotcomSearch']);
const selectedChannel = ref('DotcomSearch');
const selectedCountry = ref('KR');

const languages = ref(['en', 'ko']);
const selectedLanguage =  ref('ko');

const gptModels = ref([
  { title: 'Rubicon Search', value: 'rubicon_search' }
]);
const selectedLLMModel = ref('rubicon_search');

const msgContentRefreshKey = ref(0);
const darkMode = ref(true);
const currentMessageID = ref(null);

// Template refs
const chatWindowRef = ref(null);
const responseStarted = ref(false);

const searchResultContent = ref('');
const searchResultContentEOS = ref(false);

// query.value = '갤럭시 S25';

// selectedProductCodes.value = JSON.stringify([
//   {
//     "product_code": "SM-S938NZBFKOO",
//     "product_name": "갤럭시 S25 울트라 자급제"
//   },
//   {
//     "product_code": "SM-S937NLBBKOO",
//     "product_name": "갤럭시 S25 엣지 자급제"
//   },
//   {
//     "product_code": "SM-S937NZSBKOO",
//     "product_name": "갤럭시 S25 엣지 자급제"
//   }
// ], null, 2);

const alphaModel = reactive({
  tableUniqueID: 'productSearch',
  itemName: 'Complementation Code Mapping',
  paging: { page: 1, itemsPerPage: 10 },
  function: rubiconAdmin.productSearch.table,
  crud: [false, true, false, false],
  headerId: 'c27f873e-e986-4332-b900-dc2044e8fd8c',
  customFields: [],
  filter: {
    hideBoarder: true,
    search_words: {
      label: 'Search Words',
      type: 'text',
      selected: null,
      col: 4
    },
    excluding_search_words: {
      label: 'Excluding Search Words',
      type: 'text',
      selected: null,
      col: 4
    },
    country_code: {
      label: 'Country Code',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      selected: selectedCountry.value,
      col: 2
    },
  },
  dialogWidth: '600px',
})


// Lifecycle hooks
onMounted(() => {
  // Check if user is authenticated
  userAuthenticationCheck();

  if (import.meta.env.VITE_COUNTRY === 'UK') {
    selectedCountry.value = 'GB';
  } else {
    selectedCountry.value = 'KR';
  }
  // console.log('selectedCountry:', selectedCountry.value);
  
  initializeSessionId();

  setTimeout(() => {

    // console.log('Executed after 1 seconds');
    // console.log('authStore.username:', authStore.username);
    if (authStore.username === null || authStore.username === undefined) {
      // console.log('User is not authenticated');
      userId.value = '-';
    } else {
      // console.log('User is authenticated:', authStore.username);
      userId.value = authStore.username;
    }
    
    if (authStore.username !== null) {  
      if (authStore.username === 'alpha') {
        selectedChannel.value = 'DotcomSearch';
      } else if (authStore.username === 'debug') {
        selectedChannel.value = 'DotcomSearch';
        markdown.value = true;
      } else if (authStore.username.includes("samsung.com")) {
        selectedChannel.value = 'DotcomSearch';
      } 
    } else {
      selectedChannel.value = 'DotcomSearch';
    }
  }, 1000); // Delay of 2 seconds (2000ms)
});

onBeforeUnmount(() => {
  files.value.forEach((file) => {
    if (file.url) {
      URL.revokeObjectURL(file.url);
    }
  });
});

// Computed properties
const messageBoxLabel = computed(() => {
  return 'Model : ' + selectedLLMModel.value.toUpperCase();
});

function getComputedStyle(component) {
  if (component === 'chatWindow') {
    return themeStore.darkMode ? 'background-color: #000000' : 'background-color: #ffffff';
  }
  if (component === 'queryBox') {
    return themeStore.darkMode ? '#2f2f2f' : '#ffffff';
  }
}

// Methods
function userAuthenticationCheck() {
  if (!authStore.username) {
    console.log('User not authenticated, redirecting to login');
    router.push('/');
    return;
  }
}

function initializeSessionId() {

  // console.log('initializeSessionId');
  sessionId.value = uuidv4();
  chatDisabled.value = false

  // Make sure the user is authenticated
  userAuthenticationCheck();

  // Preserve userId from auth store
  if (authStore.username) {
    userId.value = authStore.username;
  }

}

function scroll() {
  if (chatWindowRef.value) {
    chatWindowRef.value.scrollTop = chatWindowRef.value.scrollHeight;
  }
}

function saveMessages(message) {
  const now = new Date();
  if (tempTime.value === null) {
    message.createdOn = getDatetimeString(now);
    tempTime.value = now;
  } else {
    const timeDiff = now.getTime() - tempTime.value.getTime();
    message.createdOn =
      getDatetimeString(now) + ' (' + String(timeDiff / 1000) + 'Sec)';
    tempTime.value = now;
  }

  scroll();
}

function addToSelectedProduct(item) {
  const tempSelectedProductCodes = JSON.parse(selectedProductCodes.value || '[]');
  const product = {
    product_code: item.product_code,
    product_name: item.product_name
  }
  tempSelectedProductCodes.push(product);
  selectedProductCodes.value = JSON.stringify(tempSelectedProductCodes, null, 2);
}

const { proxy } = getCurrentInstance()

async function fetchResponse() {
  currentMessageID.value = uuidv4();
  searchResultContent.value = '';
  searchResultContentEOS.value = false;
  // chatDisabled.value = true;
  const searchResults = [];
  const parsedSelectedProductCodes = JSON.parse(selectedProductCodes.value || '[]');

  for (const product of parsedSelectedProductCodes) {
    searchResults.push({
      id: product.product_code || product.id
    });
  }

  // Make sure the user is authenticated
  userAuthenticationCheck();

  // Fetch the response from the server
  const requestBody = {
    messageId: currentMessageID.value,
    model: selectedLLMModel.value,
    params: {
        channel: selectedChannel.value,
        countryCode: selectedCountry.value,
        userId: userId.value,
        message: query.value,
        lng: selectedCountry.value === "KR" ? "ko" : "en",
        guId: requestGUID.value,
        saId: requestSAID.value,
        jwtToken: jwtToken.value,
        estoreSitecode: estoreSitecode.value,
    },
    searchData: {
        searchResults: searchResults
    },
    backendCache: backendCache.value,
    updateHttpStatus: true,
    stream: streaming.value,
  };

  const response = await fetch('api/rubicon/search-summary/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestBody)
  });

  if (response.status === 401) {
    chatDisabled.value = false
    console.log('Unauthorized')
    proxy.$snackbar.showSnackbar({
      title: 'Log in required',
      message: 'You need to log in to access this feature.',
      color: 'error'
    });
    return;
  }

  if (response.status === 400 || response.status === 413 || response.status === 415) {
    chatDisabled.value = false
    console.log('Bad Request')
    const errorData = await response.json();
    console.log('Error details:', errorData);
    
    // Create a more detailed error message that shows the full structure
    let errorMessage = `Status: ${errorData.status}\nMessage: ${errorData.message}\n\nField errors:\n`;
    if (errorData.errors) {
      Object.entries(errorData.errors).forEach(([field, messages]) => {
        errorMessage += `- ${field}: ${messages.join(', ')}\n`;
      });
    }
    
    proxy.$snackbar.showSnackbar({
      title: 'Bad Request',
      message: errorMessage,
      color: 'error',
      timeout: 10000 // Show for 10 seconds
    });
    return;
  }
  
  if (streaming.value) {
    // Streaming response handling
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        console.log('SSE stream closed by server.');

        msgContentRefreshKey.value += 1;
        chatDisabled.value = false;
        responseStarted.value = false;
        break;
      }

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for await (const line of lines) {
        if (line.startsWith('data: ')) {
          // console.log(line)

          const eventData = line
            .replace('data: ', '')
            .replace(/<br\s*\/?>/gi, '\n');
          if (eventData !== 'None') {
            // await addEventData(eventData)
            // console.log(eventData)

            searchResultContent.value += eventData;
            // Check for EOS marker
            if (eventData.includes("<EOS>")) {
              console.log("EOS detected in stream");
              searchResultContentEOS.value = true;
              break;
            }
          }
        }
      }
    }
  } else {
    // Non-streaming response handling
    try {
      const responseData = await response.json();
      
      if (responseData && responseData.data) {
        searchResultContent.value = '```markdown\n' + responseData.data + '```<EOS>';
        searchResultContentEOS.value = true; // Mark as complete for non-streaming
      } else {
        console.error('No data field found in response');
        searchResultContent.value = 'Error: No data received from server';
      }
      
      msgContentRefreshKey.value += 1;
      chatDisabled.value = false;
      responseStarted.value = false;
    } catch (error) {
      console.error('Error parsing response:', error);
      searchResultContent.value = 'Error: Failed to parse server response';
      chatDisabled.value = false;
      responseStarted.value = false;
    }
  }
}



// async function sendMessage() {
//   console.log('sendMessage');
//   if (query.value === '') {
//     return
//   }
//   queryReady.value = false;

//   // API SPEC
//   alphaApiKey.value = 'CDHDFuVu.CBOPiEL9PfMB0aPW5vg8MMc2P8msytmM';
//   url.value = 'api/rubicon/search-summary/';

//   const now = new Date();
//   currentMessageID.value = uuidv4();

//   // getImages(query.value);

//   // Start fetching the SSE data
//   fetchResponse();

// }

function handleRelatedQuerySelected(selectedQuery) {
  console.log('Selected related query:', selectedQuery);
  query.value = selectedQuery;
  setTimeout(() => {
    sendMessage();
  }, 100);
}

</script>


<style scoped>
#chatMainWindow {
  overflow-y: hidden;
}

#chatPage {
  height: calc(100vh - 230px);
}
</style>

<style>
/* div.chat-select-color > div.v-input__control > div.v-input__slot > div.v-select__slot > div.v-select__selections > div {
  padding-left: 10px;
} */

#chatWindow > div > div > div.v-input__append > i {
  color: #939393;
  font-size: 36px;
}
</style>

<style>
.code-prefix {
  /* color: #000000; */
  border-radius: 5px;
  font-size: 1.0em;
  text-shadow: none;
  font-family: Menlo, Monaco, Consolas, "Andale Mono", "Ubuntu Mono", "Courier New", monospace;
  direction: ltr;
  text-align: left;
  white-space: pre;
  word-spacing: normal;
  word-break: normal;
  line-height: 1.5;
  -moz-tab-size: 4;
  -o-tab-size: 4;
  tab-size: 4;
  -webkit-hyphens: none;
  -moz-hyphens: none;
  -ms-hyphens: none;
  hyphens: none;
  text-shadow: none;
  margin: 12px 0px 12px 0px;
  overflow: auto;
  background: #22272e;
  /* background: #f2f2f2; */
}

.code-body {
  padding: 8px 12px;
  /* margin: 12px; */
}

/*
Visual Studio-like style based on original C# coloring by Jason Diamond <jason@diamond.name>
*/

code {
  font-family: Menlo, Monaco, Consolas, "Andale Mono", "Ubuntu Mono", "Courier New", monospace;
  font-weight: 400 !important;
  font-size: 0.9em !important;
}

.hljs {
  display: block;
  overflow-x: auto;
  padding: 0.5em;

  color: #cdd9e5;
  background: #22272e;
}

.hljs-comment,
.hljs-punctuation {
  color: #768390;
}

.hljs-attr,
.hljs-attribute,
.hljs-meta,
.hljs-selector-attr,
.hljs-selector-class,
.hljs-selector-id {
  color: #6cb6ff;
}

.hljs-variable,
.hljs-literal,
.hljs-number,
.hljs-doctag {
  color: #f69d50;
}

.hljs-params {
  color: #cdd9e5;
}

.hljs-function {
  color: #dcbdfb;
}

.hljs-class,
.hljs-tag,
.hljs-title,
.hljs-built_in {
  color: #8ddb8c;
}

.hljs-keyword,
.hljs-type,
.hljs-builtin-name,
.hljs-meta-keyword,
.hljs-template-tag,
.hljs-template-variable {
  color: #f47067;
}

.hljs-string,
.hljs-undefined {
  color: #96d0ff;
}

.hljs-regexp {
  color: #96d0ff;
}

.hljs-symbol {
  color: #6cb6ff;
}

.hljs-bullet {
  color: #f69d50;
}

.hljs-section {
  color: #6cb6ff;
  font-weight: bold;
}

.hljs-quote,
.hljs-name,
.hljs-selector-tag,
.hljs-selector-pseudo {
  color: #8ddb8c;
}

.hljs-emphasis {
  color: #f69d50;
  font-style: italic;
}

.hljs-strong {
  color: #f69d50;
  font-weight: bold;
}

.hljs-deletion {
  color: #ff938a;
  background-color: #78191b;
}

.hljs-addition {
  color: #8ddb8c;
  background-color: #113417;
}

.hljs-link {
  color: #96d0ff;
  font-style: underline;
}

button.copy-action {
  align-self: flex-end;
  margin: 0px 10px 0px 0px;
}

</style>