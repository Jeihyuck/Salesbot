<template>
  <div class="d-flex flex-column" style="width: 100%;">
  <div :class="locationClass" style="width: 100%;">
  <v-card
      flat style="width: 100%;"
      :style="getComputedStyle('chatCardBackground')"
  >
  <v-card-text v-if="eosDetected" class="pt-2 pl-4 pb-0 mb-n3">
    <div class="text-caption"> Model: {{ model }} | Message ID: {{ messageId }}</div>
  </v-card-text>
  <v-card-text>
    <v-row>
      <v-col cols="12">
        <div v-if="showMarkdown" v-html="renderMarkDown(content)"></div> 
        <div class="renderedHtml py-2" v-else style="font-size: 16px !important; line-height: 180% !important;" v-html="renderHtml(content)" :key="refreshKey"></div>
        <div v-if="video !== ''">
          <a :href="video.link" target="_blank">
            <img class="pl-2" :src="video.img" :alt="video.title"/>
          </a>
        </div>

        <div class="ml-2" v-if="productCard.length > 0">
          <v-row class="mb-2">
              <v-card max-width="220" v-for="(item,i) in productCard" :key="i" class="ma-1" @click="openProductUrl(productCard[i].pdpURL)">
                  <v-img
                    :width="220"
                    :src="productCard[i].images.largeImage.url"
                    cover
                  ></v-img>
                  <v-card-text>
                    <div class="text-subtitle-2 font-weight-bold pb-1">{{ productCard[i].productDisplayName }}</div>
                    <div class="text-caption text-primary">{{ productCard[i].modelCode }} ({{ productCard[i].productLaunchDate }})</div>
                    <div class="text-caption text-primary pb-1">{{ productCard[i].msrp_price_currency }} / {{ productCard[i].sale_price_currency }}</div>

                    <div class="text-caption">{{ productCard[i].uspDesc[0] }}</div>
                  </v-card-text>
              </v-card>
          </v-row>
        </div>
        <v-sheet
          class="ml-n4 pa-0"
          v-if="checkedImageList.length > 0"
          style="width: 100%; background: rgba(0,0,0,0.5);"
        >
          <v-slide-group
            v-model="selectedImages"
            class="pa-0 ma-0"
            style="width: 100%;"
            show-arrows
          >
            <v-slide-group-item
              v-for="(item,i) in checkedImageList"
              :key="i" 
              v-slot="{ isSelected, toggle, selectedClass }"
            >
              <v-card
                class='ma-1'
                height="200"
                width="200"
                @click="toggle"
              >
                <div class="d-flex fill-height align-center justify-center">
                  <v-scale-transition>
                    <a :href="item.link" target="_blank">
                      <!-- Use video tag for MP4 files -->
                      <video 
                        v-if="item.media_type === 'video' || item.media_type === 'mp4'"
                        :src="item.img" 
                        width="200" 
                        height="200"
                        preload="metadata"
                        muted
                        style="object-fit: cover;"
                      ></video>
                      <!-- Use img tag for other media types -->
                      <img 
                        v-else
                        :src="item.img" 
                        :alt="item.title"  
                        width="200" 
                        height="200"
                      />
                    </a>                    
                  </v-scale-transition>
                </div>
              </v-card>
            </v-slide-group-item>
          </v-slide-group>
        </v-sheet>
        <div v-if="relatedQuestionList.length > 0" class="mb-2">
          <v-col>
            <v-row>
              <div class="ml-2 pl-2 text-subtitle-1" style="color: #a1d2fc;">Related Questions</div>
            </v-row>
            <v-row v-for="(i, index) in relatedQuestionList.length" :key="index">
              <v-col cols="12" class="py-1">
                <v-btn 
                  class="my-0 py-0" 
                  color="grey" 
                  variant="outlined"
                  @click="handleRelatedQueryClick(relatedQuestionList[i-1])"
                >
                  {{relatedQuestionList[i-1]}}
                </v-btn>
              </v-col>
            </v-row>
          </v-col>
        </div>
        <v-row  v-if="eosDetected"  class="ml-0 mt-02 pb-2">
          <v-btn variant="text" size="x-small" icon="mdi-thumb-up-outline" :class="thumbUpClass" @click="thumbUpClick()"></v-btn>
          <v-dialog max-width="1000" v-model="dialogVisible">
            <template v-slot:activator="{ props: activatorProps }">
              <v-btn v-bind="activatorProps" variant="text" size="x-small" icon="mdi-thumb-down-outline" :class="thumbDownClass" @click="thumbDownClick()"></v-btn>
            </template>

            <template v-slot:default="{ isActive }">
              <v-card title="Please tell me in more detail.">
                <v-card-text class="pb-0">
                  <v-checkbox density="compact" hide-details
                    v-model="checkList[0]"
                    label="&nbsp;Inacurate"
                  ></v-checkbox>
                  <v-checkbox density="compact" hide-details
                    v-model="checkList[1]"
                    label="&nbsp;Irrelevant"
                  ></v-checkbox>
                  <v-checkbox density="compact" hide-details
                    v-model="checkList[2]"
                    label="&nbsp;Lack / Overflow"
                  ></v-checkbox>
                  <v-checkbox density="compact" hide-details
                    v-model="checkList[3]"
                    label="&nbsp;Etc"
                  ></v-checkbox>
                  <v-textarea
                    v-shortkey.avoid
                    v-model="comment"
                    variant="outlined"
                    density="compact"
                    base-color="grey-darken-1"
                    hide-details
                    class="mt-4"
                    label="Write your comment"
                  ></v-textarea>
                </v-card-text>

                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn
                    text="Submit"
                    variant="tonal"
                    class="my-2"
                    @click="sendAppraisal()"
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

          <v-dialog max-width="1800" v-model="dialogDebug">
            <template v-slot:activator="{ props: activatorProps }">
              <v-btn v-bind="activatorProps" variant="text" size="x-small" icon="mdi-code-json" class="text-grey ml-n1" @click="checkDebug()"></v-btn>
            </template>

            <template v-slot:default="{ isActive }">
              <v-card title="Debug">
                <v-card-text class="pb-0">
                  <div class="text-subtitle-1">Time Logs</div>
                  <div class="renderedHtml ml-n3 pr-2" v-html="timeLogs"></div>
                  <br>
                  <div class="text-subtitle-1">Debug Content</div>
                  <codemirror
                    v-model="debugContent"
                    :style="{ borderRadius: '6px', border: '1px solid #444444' }"
                    :autofocus="true"
                    :lineWrapping="true"
                    :indent-with-tab="true"
                    :tab-size="2"
                    :extensions="getJsonExtensions()"
                  />
                </v-card-text>

                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn
                    text="Close"
                    variant="tonal"
                    class="mr-4 my-4"
                    @click="close()"
                  ></v-btn>
                </v-card-actions>
              </v-card>
            </template>
          </v-dialog>
        </v-row>
      </v-col>
    </v-row>
  </v-card-text>
  </v-card>
  </div>
  </div>
</template>


<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { marked } from 'marked'
import { renderMarkDown } from '@/_helpers'
import { Codemirror } from 'vue-codemirror'
import { rubicon } from '@/_services'
import { useEnvStore } from '@/stores/env'
import { EditorView } from "@codemirror/view"
import Blinker from '@/components/chat/Blinker.vue'
import { useThemeStore } from '@/stores/theme'
// import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'
import { json, jsonParseLinter } from '@codemirror/lang-json'
// import { markdown } from '@codemirror/lang-markdown'
import { vscodeDark } from '@uiw/codemirror-theme-vscode'
import { linter } from '@codemirror/lint'
import axios from 'axios'
import { provideSelection } from 'vuetify/lib/components/VDataTable/composables/select.mjs'

defineOptions({
  inheritAttrs: false
})

const themeStore = useThemeStore()
const envStore = useEnvStore()
const props = defineProps({
  content: {
    required: true
  },
  requestQuery: {
    required: false,
    // default: ''
  },
  model: {
    required: true
  },
  channel: {
    type: String,
    required: true
  },
  countryCode: {
    type: String,
    required: true
  },
  contentKey: {
    type: Number,
    default: 0
  },
  messageId: {
    required: true
  },
  showMarkdown: {
    required: true
  },
  eosDetected: {
    required: false,
  },
  defaultGreeting: {
    type: Boolean,
    required: false,
  },
})

const emit = defineEmits(['relatedQuerySelected']);

// Reactive state
const selectedImages = ref(null)
const thumbUp = ref(false)
const thumbDown = ref(false)
const checkList = reactive([false, false, false, false, false, false])
const comment = ref('')
const dialogVisible = ref(false)
const dialogReference = ref(false)
const dialogDebug = ref(false)
const timeLogs = ref('')
const debugContent = ref('')
const unstructredContent = ref('')
const specTable = ref('')
const viteOpType = ref('')
const refreshKey = ref(0)
const checkedImageList = ref([]);
const relatedQuestionList = ref([]);
const video = ref({'link': '', 'img': '', 'title': ''});
const productCard = ref('');

const getJsonExtensions = () => {
  return [json(), vscodeDark, linter(jsonParseLinter()), EditorView.lineWrapping]
}

function openProductUrl(url) {
  if (url) {
    window.open(url, '_blank');
  }
}

function getComputedStyle(component) {
  if (component === 'chatCardText') {
    return '#000000'
    // if (themeStore.darkMode) {
    //   return '#000000'
    // } else {
    //   return '#ffffff'
    // }
  }
  if (component === 'chatCardBackground') {
    if (themeStore.darkMode) {
      return 'background-color: #000000'
    } else {
      return 'background-color: #f0f6ff'
    }
  }
}

// Computed properties
const locationClass = computed(() => {
  return 'd-flex justify-end pa-3'
})

const thumbUpClass = computed(() => {
  return thumbUp.value ? 'text-primary' : 'text-grey'
})

const thumbDownClass = computed(() => {
  return thumbDown.value ? 'text-primary ml-n1' : 'text-grey ml-n1'
})

const { proxy } = getCurrentInstance()
// Methods
async function sendAppraisal() {
  // console.log('send appraisal')

  if (comment.value.trim() === '') {
    proxy.$snackbar.showSnackbar({
      title: 'Comment',
      message: 'Please write a comment, it is required for appraisal',
      color: 'warning'
    });
  } else {
    const selection = []
    for (let i = 0; i < checkList.length; i++) {
      if (checkList[i]) {
        selection.push(i)
      }
    }

    const requestBody = {
        messageId: props.messageId,
        channel: props.channel,
        countryCode: props.countryCode,
        thumbUp: false,
        comment: comment.value,
        selectedList: selection,
    };
            

    const response = await fetch('api/rubicon/appraisal-registry/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    });
  }

  dialogVisible.value = false
}

function cancel() {
  dialogVisible.value = false
}

function close() {
  dialogReference.value = false
  dialogDebug.value = false
}

watch(
  () => props.content,
  (newValue, oldValue) => {
    if (newValue == '') {
      // console.log('props.searchResultContent changed:', newValue);
      productCard.value = '';
      checkedImageList.value = [];
      relatedQuestionList.value = [];
    }
  }
)


watch(
  () => props.requestQuery,
  (newValue, oldValue) => {
    console.log('requestQuery', newValue)
    if (newValue !== '' || newValue !== undefined) {
      const url = 'api/rubicon/supplementaryinfo/';

      const supplementaryParams = {
        messageId: props.messageId,
        supplementInfo: [
          // {
          //     "supplementType": "media",
          //     "supplementCount": 6,
          //     "timeout": 5
          // },
          // {
          //     "supplementType": "product_card",
          //     "supplementCount": 7,
          //     "timeout": 5
          // },
          // {
          //     "supplementType": "related_query",
          //     "supplementCount": 3,
          //     "timeout": 5
          // },
          {
              "supplementType": "hyperlink",
              "supplementCount": 5,
              "timeout": 5
          }
        ]
      };
      axios.post(url, supplementaryParams)
        .then(response => {
          // Process all supplement types from a single response
          if (response.data && response.data.data) {
            // Find and process media data
            const mediaData = response.data.data.find(item => item.supplement_type === 'media');
            if (mediaData && mediaData.data) {
              checkedImageList.value = mediaData.data;
              console.log('media:', mediaData.data);
            }
            
            // Find and process product card data
            const productCardData = response.data.data.find(item => item.supplement_type === 'product_card');
            if (productCardData && productCardData.data && productCardData.data.length > 0) {
              productCard.value = productCardData.data;
              console.log('product_card:', productCardData.data);
            }
            
            // Find and process related query data
            // const relatedQueryData = response.data.data.find(item => item.supplement_type === 'related_query');
            // if (relatedQueryData && relatedQueryData.data) {
            //   relatedQuestionList.value = relatedQueryData.data.map(item => item.related_query);
            //   console.log('related_query:', relatedQueryData.data);
            // }
            
            // Find and process hyperlink data if needed
            const hyperlinkData = response.data.data.find(item => item.supplement_type === 'hyperlink');
            if (hyperlinkData && hyperlinkData.data) {
              console.log('hyperlink:', hyperlinkData.data);
              // Process hyperlinks if needed
            }
          }
        })
        .catch(error => {
          console.error('Error:', error);
        });
    }
  },
  { deep: true }
);

watch(
  () => props.eosDetected,
  (newValue, oldValue) => {
    console.log('EOS Detected:', newValue, oldValue);
    if (newValue === true && !oldValue) {
      console.log('EOS detected, fetching related_query_v2, product_card_v2, and media_v2 data');
      
      const url = 'api/rubicon/supplementaryinfo/';
      
      // If defaultGreeting is true, set the supplement info to 'greeting_query', otherwise use 'related_query_v2', 'product_card_v2', and 'media_v2'
      let supplementInfo = []
      if (props.defaultGreeting) {
        supplementInfo = [
          {
            "supplementType": "greeting_query",
            "supplementCount": 3,
            "timeout": 5
          }
        ]
      } else {
        supplementInfo = [
          {
            "supplementType": "related_query_v2",
            "supplementCount": 3,
            "timeout": 5
          },
          {
            "supplementType": "product_card_v2",
            "supplementCount": 7,
            "timeout": 10
          },
          {
            "supplementType": "media_v2",
            "supplementCount": 6,
            "timeout": 10
          }
        ]
      }
      
      const supplementaryParams = {
        messageId: props.messageId,
        supplementInfo: supplementInfo
      };
      
      axios.post(url, supplementaryParams)
        .then(response => {
          if (response.data && response.data.data && props.defaultGreeting) {
            // Find and process greeting query data
            const greetingQueryData = response.data.data.find(item => item.supplement_type === 'greeting_query');
            if (greetingQueryData && greetingQueryData.data) {
              relatedQuestionList.value = greetingQueryData.data.map(item => item.greeting_query);
              console.log('greeting_query:', greetingQueryData.data);
            }
          } else {
            // Find and process related_query_v2 data
            const relatedQueryV2Data = response.data.data.find(item => item.supplement_type === 'related_query_v2');
            if (relatedQueryV2Data && relatedQueryV2Data.data) {
              relatedQuestionList.value = relatedQueryV2Data.data.map(item => item.related_query);
              console.log('related_query_v2:', relatedQueryV2Data.data);
            }
            // Find and process product_card_v2 data
            const productCardData = response.data.data.find(item => item.supplement_type === 'product_card_v2');
            if (productCardData && productCardData.data && productCardData.data.length > 0) {
              productCard.value = productCardData.data;
              console.log('product_card_v2:', productCardData.data);
            }
            // Find and process media_v2 data
            const mediaData = response.data.data.find(item => item.supplement_type === 'media_v2');
            if (mediaData && mediaData.data && mediaData.data.length > 0) {
              checkedImageList.value = mediaData.data;
              console.log('media_v2:', mediaData.data);
            }
          }
        })
        .catch(error => {
          console.error('Error fetching related_query_v2:', error);
        });
    }
  }
);

function checkReference() {
  const query = {
    message_id: props.messageId
  }
  rubicon.appraisal.function('get_reference_document', query).then(response => {
    console.log(response.data.unstructred_content)
    console.log(response.data.spec_table)
    unstructredContent.value = JSON.stringify(response.data.unstructred_content, null, 2)
    specTable.value = renderHtml(response.data.spec_table)
  })
}

function checkDebug() {
  const query = {
    message_id: props.messageId
  }
  rubicon.appraisal.function('get_debug', query).then(response => {
    // console.log(response.data.timing_logs)
    timeLogs.value = renderHtml(response.data.timing_logs)
    debugContent.value = JSON.stringify(response.data.debug_content, null, 2)  
  })
}

function thumbUpClick() {
  thumbUp.value = true
  thumbDown.value = false
  const query = {
    message_id: props.messageId,
    thumb_up: true,
  }
  rubicon.appraisal.function('ut_appraisal', query).then(() => {
    dialogVisible.value = false
  })
}

function thumbDownClick() {
  thumbUp.value = false
  thumbDown.value = true
}

function renderMarkdownContent(text) {
  return renderMarkDown(text || '')
}

const markdownContent = ref(`# Hello World

This is a **Markdown** example.`)


function renderHtml(text) {
  // console.log(text.replace("```markdown", "").replace("```", ""))
  if (text === null) {
    return ''
  } else {
    return marked(text.replace("```markdown", "").replace("```", ""))
  }
}

async function copyToClipboard(textToCopy) {
  // Navigator clipboard API needs a secure context (HTTPS)
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(textToCopy)
  } else {
    // Use a hidden textarea for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = textToCopy
    textArea.style.position = 'absolute'
    textArea.style.left = '-999999px'
    document.body.prepend(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
    } catch (error) {
      console.error(error)
    } finally {
      textArea.remove()
    }
  }
}

async function handleRelatedQueryClick(query) {
  console.log('Related query clicked:', query);
  
  // Copy to clipboard
  await copyToClipboard(query);
  
  // Show notification that text was copied
  if (proxy && proxy.$snackbar) {
    proxy.$snackbar.showSnackbar({
      title: 'Copied',
      message: 'Query copied to clipboard',
      color: 'info'
    });
  }
  
  // Send to parent component
  emit('relatedQuerySelected', query);
}

// Lifecycle hooks
onMounted(() => {
  // viteOpType.value = import.meta.env.VITE_OP_TYPE
});
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
