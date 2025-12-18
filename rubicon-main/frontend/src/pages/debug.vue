<template>
  <!-- ######## Below Code is for Mobile ############################################################################################################################################### -->
  <v-row v-if="envStore.isMobile" class="pt-2" id='chatMainWindow' :style="getComputedStyle('chatWindow')">

    <v-col id="chatWindow" style="height: calc(100vh - 72px); overflow-y: auto;">
      <v-row v-for="(message, index) in conversation.messages" :key="index">
        <msg-content
        class="mx-2 my-0"
        v-show="(debug===true && message.isDebug ===true) || message.isDebug === false"
            :content="message.content"
            :model="message.model"
            :key="message.key"
            :type="message.type"
            :isBot="message.isBot"
            :isDebug="message.isDebug"
            :createdOn="message.createdOn"
            :loadingMessage="message.loadingMessage"
            :messageId="message.messageId"
            :completed="message.completed"
            :selectedLLMModel="selectedLLMModel"
            :markdown="markdown"
          />
      </v-row>
      <v-row class="py-10"></v-row>


      <v-container fluid style="position: fixed; bottom: 0px; width: calc(100vw - 2vw); z-index: 1;">
        <v-row class="mb-1">
          <v-col
            v-for="(file, i) in files"
            :key="i"
            cols="auto"
            class="pr-0"
          >
            <v-card class="mx-auto">
              <div style="position: relative;">
                <!-- Image preview -->
                <v-img
                  v-if="file.type.startsWith('image/')"
                  :src="file.dataUrl || file.url"
                  height="100"
                  width="100"
                  cover
                >
                  <v-icon @click="removeFile(i)" size="16" color="black" style="position: absolute; top: 0; right: 0;" icon="mdi-close-box"></v-icon>
                </v-img>
                
                <!-- Audio preview -->
                <div v-else-if="file.type.startsWith('audio/')" class="pa-2">
                  <v-icon size="48" icon="mdi-file-music-outline"></v-icon>
                  <div class="text-caption">{{ file.name }}</div>
                  <audio v-if="file.url" controls style="width: 200px">
                    <source :src="file.url" :type="file.type">
                  </audio>
                  <v-icon @click="removeFile(i)" size="16" color="black" style="position: absolute; top: 0; right: 0;" icon="mdi-close-box"></v-icon>
                </div>
              </div>
            </v-card>
          </v-col>
        </v-row>
        <file-upload
          extensions="gif,jpg,jpeg,png,webp,mp3,wav,m4a,ogg"
          accept="image/png,image/gif,image/jpeg,image/webp,audio/mpeg,audio/wav,audio/mp4,audio/ogg"
          :multiple="true"
          v-model="files"
          @input-filter="inputFilter"
          @input-file="inputFile"
          ref="fileUploadRef"
          style="display: none;">
        </file-upload>
        <v-textarea
          auto-grow
          :disabled="chatDisabled"
          class=""
          bg-color="#2f2f2f"
          :label="messageBoxLabel"
          persistent-placeholder
          placeholder="Message"
          hide-details
          v-model="query"
          prepend-inner-icon="mdi-paperclip"
          rows="1"
          variant="solo-filled"
          append-icon="mdi-arrow-up-bold-circle"
          @click:append="sendMessage"
          @click:prepend-inner="triggerFileUpload"
        />
      </v-container>
  </v-col>
  </v-row>

  <!-- ######## Below Code is for PC ############################################################################################################################################### -->
  <v-row v-if="!envStore.isMobile" class="pt-2" id='chatMainWindow'>
    <v-col cols="2">
      <div class="pl-3 pt-6 pb-1"  style="font-weight: bold;">GPT Model</div>
      <v-select
        class="px-1 pt-1"
        hide-details
        variant="outlined"
        density="compact"
        lable="GPT Model"
        :items="gptModels"
        v-model="selectedLLMModel"
      >
      </v-select>
      <div class="pl-3 pt-3 pb-1"  style="font-weight: bold;">Channel</div>
      <v-select
        class="px-1 pt-1"
        hide-details
        variant="outlined"
        density="compact"
        lable="Channel"
        :items="channels"
        v-model="selectedChannel"
      >
      </v-select>
      <div class="pl-3 pt-3 pb-1"  style="font-weight: bold;">Country</div>
      <v-select
        class="px-1 pt-1"
        hide-details
        variant="outlined"
        density="compact"
        lable="Country"
        :items="countrys"
        v-model="selectedCountry"
      >
      </v-select>
      <v-switch
        class="pl-2 pt-1 pb-0"
        color="primary"
        v-model="markdown"
        :label="`Markdown: ${markdown ? 'On' : 'Off'}`"
        hide-details
      ></v-switch>
      <v-switch
        class="pl-2 pt-0 mt-n2"
        color="primary"
        v-model="themeStore.darkMode"
        :label="`Dark Mode: ${darkMode ? 'On' : 'Off'}`"
        hide-details
      ></v-switch>
      <div class="mt-4 mx-1">
        <v-btn block variant="tonal" prepend-icon="mdi-broom" @click="initializeSessionId()">
          <template v-slot:prepend>
            <v-icon color="primary"></v-icon>
          </template>
        &nbsp;New Chat</v-btn>
      </div>
      <v-divider class="mx-2 mt-4 mb-2" color="white"></v-divider>
      <div class="pl-3 pt-0 pb-0"  style="font-weight: bold;">Chat History</div>
      <v-col class="px-0 mx-0" style="height: calc(100vh - 450px); overflow-y: auto;">
        <v-row class="ma-0 pa-0" v-for="(message, index) in userChathistory" :key="index">
          <MsgHistory class="mt-0 mb-2 ml-1 mr-2" :message="message" :darkMode="darkMode" :userId="userId"></MsgHistory>
        </v-row>
      </v-col>
    </v-col>
    <v-col cols="10" id="chatWindow" style="height: calc(100vh - 72px); overflow-y: auto;" :style="getComputedStyle('chatWindow')">
      <v-row v-for="(message, index) in conversation.messages" :key="index">
        <msg-content
        class="mx-4 my-0"
        v-show="(debug===true && message.isDebug ===true) || message.isDebug === false"
            :content="message.content"
            :model="message.model"
            :key="message.key"
            :type="message.type"
            :isBot="message.isBot"
            :isDebug="message.isDebug"
            :createdOn="message.createdOn"
            :messageId="message.messageId"
            :completed="message.completed"
            :loadingMessage="message.loadingMessage"
            :selectedLLMModel="selectedLLMModel"
            :markdown="markdown"
            :darkMode="darkMode"
          />
      </v-row>
      <v-row class="py-10"></v-row>


      <v-container fluid style="position: fixed; bottom: 0px; width: calc(100vw - (100vw / 6)); z-index: 1;">
        <v-row class="mb-1">
          <v-col
            v-for="(file, i) in files"
            :key="i"
            cols="auto"
            class="pr-0"
          >
            <v-card class="mx-auto">
              <div style="position: relative;">
                <!-- Image preview -->
                <v-img
                  v-if="file.type.startsWith('image/')"
                  :src="file.dataUrl || file.url"
                  height="100"
                  width="100"
                  cover
                >
                  <v-icon @click="removeFile(i)" size="16" color="black" style="position: absolute; top: 0; right: 0;" icon="mdi-close-box"></v-icon>
                </v-img>
                
                <!-- Audio preview -->
                <div v-else-if="file.type.startsWith('audio/')" class="pa-2">
                  <v-icon size="48" icon="mdi-file-music-outline"></v-icon>
                  <div class="text-caption">{{ file.name }}</div>
                  <audio v-if="file.url" controls style="width: 200px">
                    <source :src="file.url" :type="file.type">
                  </audio>
                  <v-icon @click="removeFile(i)" size="16" color="black" style="position: absolute; top: 0; right: 0;" icon="mdi-close-box"></v-icon>
                </div>
              </div>
            </v-card>
          </v-col>
        </v-row>
        <file-upload
          extensions="gif,jpg,jpeg,png,webp,mp3,wav,m4a,ogg"
          accept="image/png,image/gif,image/jpeg,image/webp,audio/mpeg,audio/wav,audio/mp4,audio/ogg"
          :multiple="true"
          v-model="files"
          @input-filter="inputFilter"
          @input-file="inputFile"
          ref="fileUploadRef"
          style="display: none;">
        </file-upload>
        <v-textarea
          auto-grow
          :disabled="chatDisabled"
          class="pr-8"
          :bg-color="getComputedStyle('queryBox')"
          :label="messageBoxLabel"
          persistent-placeholder
          placeholder="Message (Ctrl+Enter to send)"
          hide-details
          v-model="query"
          prepend-inner-icon="mdi-paperclip"
          rows="1"
          :focused="textareaFocused"
          variant="solo-filled"
          append-icon="mdi-arrow-up-bold-circle"
          @click:append="sendMessage"
          @click:prepend-inner="triggerFileUpload"
        />
      </v-container>

      <div style="display: none" v-shortkey="['ctrl', 'enter']" @shortkey.propagate="sendMessage"></div>
  </v-col>
  </v-row>
</template>

<script setup>

import FileUpload from 'vue-upload-component';
import MsgContent from '@/components/chat/MsgContent';
import MsgHistory from '@/components/chat/MsgHistory';
import 'github-markdown-css';
import { v4 as uuidv4 } from 'uuid';
import { rubiconAdmin } from '@/_services';
import { useAuthStore } from '@/stores/auth';
import { getDatetimeString } from '@/_helpers';
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue';
import { useEnvStore } from '@/stores/env'
import { useThemeStore } from '@/stores/theme'


const themeStore = useThemeStore()

const envStore = useEnvStore()

const components = { FileUpload }
const authStore = useAuthStore()
const textareaFocused = ref(false);

// Reactive state variables
const markdown = ref(true);
const chatDisabled = ref(false);
const conversation = reactive({
  messages: [],
});

const files = ref([]);
const alphaApiKey = ref('');
const url = ref('');
const formData = ref(new FormData());
const queryReady = ref(false);
const query = ref('');
const sessionId = ref('');
const userId = ref('-');
const tempTime = ref(null);
const countrys = ref(['GB', 'KR']);
const channels = ref(['UT-Test-20241112', 'Security Test', 'DEV Test', 'DEV Debug']);
const selectedChannel = ref('DEV Debug');
const selectedCountry = ref('KR');

const gptModels = ref([
  { title: 'Rubicon', value: 'rubicon' },
  { title: 'Rubicon Debug', value: 'rubicon_debug' },
  { title: 'Rubicon Test', value: 'rubicon_test' },
  { title: 'gpt-4o-mini', value: 'gpt-4o-mini' },
  { title: 'gpt-4o', value: 'gpt-4o' },
]);
const selectedLLMModel = ref('rubicon_debug');
const userChathistory = ref([]);
// const debugStatus = ref([
//   { title: 'True', value: true },
//   { title: 'False', value: false },
// ]);
const debug = ref(false);
// const chatUUID = ref(null);
// const eventSource = ref(null);
const currentMessageID = ref(null);

// Template refs
const fileUploadRef = ref(null);
const chatWindowRef = ref(null);

const refreshMsgHistory = () => {
  console.log('refreshMsgHistory');
  const query = {
    userId: authStore.username,
  }
  rubiconAdmin.chat.function('get_chat_history', query).then((response)=> {
    userChathistory.value = response.data;
  })
}

// Lifecycle hooks
onMounted(() => {
  initializeSessionId();
  // conversation.messages =  [
  //   { type:"text", messageId: "d593ac3d-e413-4ad4-81bf-455d5d6055b1", content :"안녕", role :"user", createdOn:"2024-12-10 15:54:00", isDebug:false, isBot:false,model:"rubicon"},
  //   { type:"text", messageId: "5c29b01c-0b56-4fe2-b75e-e3248181bd63", content:"```markdown\n안녕하세요! 삼성 제품이나 서비스에 대해 궁금한 점이 있으시면 언제든지 말씀해 주세요. \n\n삼성의 다양한 기능과 서비스에 대해 안내해 드릴 수 있습니다. 예를 들어, 삼성페이와 관련된 정보나 갤럭시 기기의 사용법 등 여러 가지를 도와드릴 수 있어요. \n\n더 궁금한 점이 있으시면 언제든지 질문해 주세요! \n\n![Galaxy Buds Series showcasing translation feature with Galaxy AI and Auracast.](https://dev-img-kr.samsunggenai.com/images/%5BSales%20Talk%5D%208.%20Use%20Cases_Galaxy%20Buds%20series_%28Buds2%20Pro%2C%20Buds2%2C%20Buds%20FE%29_with%20Galaxy%20AI_v1.0_240227/3/1.png)\n### 답변 출처 \n\n- <a href=\"https://www.samsung.com/sec/apps/samsung-wallet/#page=4\" target=\"_blank\">출처 1</a>\n- <a href=\"https://dev-img-kr.samsunggenai.com/pvi-pdf/2024%20TV%20Feature%20Book_v1.1_240221.pdf#page=53\" target=\"_blank\">출처 2</a>\n```<EOS>","role":"system","createdOn":"2024-12-10 15:54:00 (0.001Sec)", key:0, isBot:true, model:"rubicon", loadingMessage:"__vue_devtool_undefined__", completed:true }
  // ]

  setTimeout(() => {
    refreshMsgHistory();
    console.log('Executed after 1 seconds');
    console.log('authStore.username:', authStore.username);
    userId.value = authStore.username;
    if (authStore.username !== null) {  
      if (authStore.username === 'alpha') {
        selectedChannel.value = 'DEV Debug';
      } else if (authStore.username === 'debug') {
        selectedChannel.value = 'DEV Test';
        markdown.value = true;
      } else if (authStore.username.includes("samsung.com")) {
        selectedChannel.value = 'UT-Test-20241112';
      } 
    } else {
      selectedChannel.value = 'UT-Test-20241112';
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


// watch(() => themeStore.darkMode, (newName, oldName) => {
//   console.log(darkMode)
//   themeStore.setDarkMode(darkMode.value)
// });

// Methods
function triggerFileUpload() {
  if (fileUploadRef.value) {
    const fileInput = fileUploadRef.value.$el.querySelector('input[type="file"]')
    if (fileInput) {
      fileInput.click()
    } else {
      console.error('File input element not found')
    }
  } else {
    console.error('File upload reference not found')
  }
}

function removeFile(index) {
  files.value.splice(index, 1);
}

async function inputFilter(newFile, oldFile, prevent) {
  if (newFile && !oldFile) {
    // Check for system files/folders
    if (/(\/|^)(Thumbs\.db|desktop\.ini|\..+)$/.test(newFile.name)) {
      return prevent()
    }

    // Check for dangerous file types
    if (/\.(php5?|html?|jsx?)$/i.test(newFile.name)) {
      return prevent()
    }

    // Check for allowed file types
    const allowedTypes = {
      // Images
      'image/jpeg': true,
      'image/png': true,
      'image/gif': true,
      'image/webp': true,
      // Audio
      'audio/mpeg': true,  // mp3
      'audio/wav': true,   // wav
      'audio/mp4': true,   // m4a
      'audio/ogg': true    // ogg
    };

    if (!allowedTypes[newFile.type]) {
      console.warn('File type not allowed:', newFile.type);
      return prevent();
    }

    //Add file size limit
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (newFile.size > maxSize) {
      console.warn('File too large:', newFile.size);
      return prevent();
    }
  }
}

function inputFile(newFile, oldFile) {
  if (newFile && !oldFile) {
    // Handle different file types
    if (newFile.file) {
      if (newFile.type.startsWith('image/')) {
        // Handle image files
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            newFile.dataUrl = e.target.result;
          } catch (error) {
            console.error('Error creating image data URL:', error);
          }
        };
        reader.readAsDataURL(newFile.file);
      } else if (newFile.type.startsWith('audio/')) {
        // Handle audio files
        // Create an audio URL for preview if needed
        newFile.url = URL.createObjectURL(newFile.file);
        // Optional: Add audio metadata
        newFile.isAudio = true;
      }
    }
  }
  
  // Cleanup when file is removed
  if (!newFile && oldFile) {
    if (oldFile.url) {
      URL.revokeObjectURL(oldFile.url);
    }
  }
}

function initializeSessionId() {
  // console.log('initializeSessionId');
  sessionId.value = uuidv4();
  chatDisabled.value = false
  conversation.messages = [];

  defaultGreeting();
}

// function initialize() {
//   tempTime.value = null;
// }

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

  conversation.messages.push(message);
  scroll();
}

function getMessageHistory(messages) {
  return messages.map((message) => ({
    type: message.type || 'text',
    messageId: message.messageId,
    role: message.role,
    createdOn: message.createdOn || new Date().toISOString(),
    content:
      message.role === 'system'
        ? cleanupSystemMessage(message.content)
        : message.content,
  }));
}

function cleanupSystemMessage(content) {
  if (!content) return '';

  // Split by newlines and find the line after "Final Answer"
  const lines = content.split('\n');
  let foundAnswer = false;
  let answer = '';

  for (const line of lines) {
    if (foundAnswer && line.includes('------------')) {
      break;
    }
    if (foundAnswer) {
      answer = line.trim();
    }
    if (line.includes('Final Answer')) {
      foundAnswer = true;
    }
  }

  // If no special patterns were found, return the original content
  if (!answer) {
    return content.trim();
  }

  // Remove any *\n or * from the beginning of the answer
  return answer.replace(/^\*\\n/, '').replace(/^\*/, '').trim();
}
const { proxy } = getCurrentInstance()

async function fetchResponse() {
  chatDisabled.value = true
  const answer = {
    type: 'text',
    messageId: currentMessageID.value,
    content: '',
    role: 'system',
    createdOn: '',
    key: 0,
    isBot: true,
    model: selectedLLMModel.value,
    loadingMessage: null,
    completed: false,
  };
  saveMessages(answer);

  const response = await fetch(url.value, {
    method: 'POST',
    headers: {
      Authorization: `apiKey ${alphaApiKey.value}`,
    },
    body: formData.value,
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
  
  if (!response.ok) {
    console.error('Failed to connect:', response.statusText);
    chatDisabled.value = false
    return;
  }

  query.value = '';

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      console.log('SSE stream closed by server.');
      conversation.messages[conversation.messages.length - 1].completed = true;
      chatDisabled.value = false
      setTimeout(() => {
        refreshMsgHistory();
      }, 500);
      break;
    }

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('audio: ')) {
        const eventData = line
          .replace('audio: ', '')
          .replace(/<br\s*\/?>/gi, '\n');
        if (eventData !== 'None') {
          conversation.messages[
            conversation.messages.length - 2
          ].content += eventData;
        }
      }
      if (line.startsWith('data:[loading]')) {
        const eventData = line
          .replace('data:[loading]', '')
          .replace(/<br\s*\/?>/gi, '\n');

        console.log(eventData)
        if (eventData !== 'None') {
          conversation.messages[
            conversation.messages.length - 1
          ].loadingMessage = eventData;
        }
      }
      if (line.startsWith('data: ')) {
        console.log(line)
        conversation.messages[
          conversation.messages.length - 1
        ].loadingMessage = undefined;
        const eventData = line
          .replace('data: ', '')
          .replace(/<br\s*\/?>/gi, '\n');
        if (eventData !== 'None') {
          conversation.messages[
            conversation.messages.length - 1
          ].content += eventData;
          await new Promise((resolve) => setTimeout(resolve, 0));
        }
      }
    }
    scroll();
  }
}

async function sendMessage() {
  console.log('sendMessage');
  if (query.value === '') {
    return
  }
  console.log('send message');
  queryReady.value = false;

  // API SPEC
  alphaApiKey.value = 'CDHDFuVu.CBOPiEL9PfMB0aPW5vg8MMc2P8msytmM';
  url.value = 'api/rubicon/completion/';

  formData.value = new FormData();

  const meta = {
    agentId: '100110257',
    agentName: 'Ghiel De Leon',
    countryCode: selectedCountry.value
  };

  const messageHistory = getMessageHistory(conversation.messages);

  const now = new Date();
  currentMessageID.value = uuidv4();
  const message = [
    {
      type: 'text',
      messageId: currentMessageID.value,
      content: query.value,
      role: 'user',
      createdOn:
        tempTime.value === null
          ? getDatetimeString(now)
          : getDatetimeString(now) +
            ' (' +
            String((now.getTime() - tempTime.value.getTime()) / 1000) +
            'Sec)',
    },
  ];

  formData.value.append('channel', selectedChannel.value);
  formData.value.append('model', selectedLLMModel.value);
  formData.value.append('meta', JSON.stringify(meta));
  formData.value.append('userId', 'debug');
  formData.value.append('department', authStore.department);
  formData.value.append('sessionId', sessionId.value);
  formData.value.append('messageHistory', JSON.stringify(messageHistory));
  formData.value.append('message', JSON.stringify(message));
  formData.value.append('lng', 'en');
  formData.value.append('showLoading', 'true');

  for (let i = 0; i < files.value.length; i++) {
    // The actual file is stored in the 'file' property of each file object
    if (files.value[i].file) {
      formData.value.append('files', files.value[i].file);
    }
  }

  const queryMessage = {
    type: 'text',
    messageId: uuidv4(),
    content: query.value,
    role: 'user',
    createdOn: '',
    isDebug: false,
    isBot: false,
    model: selectedLLMModel.value,
  };
  saveMessages(queryMessage);


  // Start fetching the SSE data
  fetchResponse();

  // Clear files after sending
  files.value = [];
}

async function defaultGreeting() {

  console.log('get default greeting message');

  alphaApiKey.value = 'CDHDFuVu.CBOPiEL9PfMB0aPW5vg8MMc2P8msytmM';
  url.value = 'api/rubicon/completion/';

  formData.value = new FormData();

  const meta = {
    countryCode: selectedCountry.value
  };

  // const messageHistory = getMessageHistory(conversation.messages);

  const now = new Date();
  currentMessageID.value = uuidv4();
  const message = [
    {
      type: 'text',
      messageId: currentMessageID.value,
      content: query.value,
      role: 'user',
      createdOn:
        tempTime.value === null
          ? getDatetimeString(now)
          : getDatetimeString(now) +
            ' (' +
            String((now.getTime() - tempTime.value.getTime()) / 1000) +
            'Sec)',
    },
  ];

  formData.value.append('channel', '-');
  formData.value.append('model', 'default_greeting');
  formData.value.append('meta', JSON.stringify(meta));
  formData.value.append('userId', userId.value);
  formData.value.append('department', authStore.department);
  formData.value.append('sessionId', sessionId.value);
  formData.value.append('messageHistory', JSON.stringify([]));
  formData.value.append('message', JSON.stringify(message));
  formData.value.append('lng', 'en');
  formData.value.append('showLoading', 'false');

  fetchResponse();
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