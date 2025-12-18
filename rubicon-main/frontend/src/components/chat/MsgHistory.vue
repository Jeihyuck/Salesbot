<template>
  <v-row class="d-flex flex-column">
    <v-dialog v-model="msgHistoryVisible" max-width="1200">
      <template v-slot:activator="{ props: activatorProps }">
        <v-card class="px-4 py-4" v-bind="activatorProps"> {{ shortenMessage }}</v-card>
      </template>

      <template v-slot:default="{ isActive }">
        <v-card title="Chat History">
          <v-card-text class="pb-0 mb-4 mt-4">
            <div style="color: #6d94c7">{{message.message}}</div>
          </v-card-text>
          <v-card-text>
            <!-- <div> {{ message.output }}</div> -->
            <div class="renderedHtml" v-html="renderHtml(message.output)"></div>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              text="Close"
              @click="isActive.value = false"
            ></v-btn>
          </v-card-actions>
        </v-card>
      </template>
    </v-dialog>
  </v-row>
</template>

<script setup>
import { marked } from 'marked'
import { ref } from 'vue'

const props = defineProps({
  message: Object,
  darkMode: Boolean
})

const msgHistoryVisible = ref(false);

watch(() => msgHistoryVisible, (newName, oldName) => {
  console.log(msgHistoryVisible)
  console.log(props.message)
  console.log(`Name changed from ${oldName} to ${newName}`);
});

const shortenMessage = computed(() => {
  if (props.message.message.length < 30) {
    return props.message.message
  } else {
    return props.message.message.substring(0, 30) + '...'
  }

  
})


function renderHtml(text) {
  try {
    if (text === null) {
      return ''
    } else {
      return marked(text.replace("```markdown", "").replace("```", ""))
    }
  } catch (error) {
    return "Response had an error";
  } 

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
  padding: 20px;
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

:deep(.renderedHtml > table, th, td) {
  border: 1px #838383 solid;

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
  padding-left: 20px;
}

:deep(.renderedHtml > ul > li > ul) {
  padding-left: 20px;

}

:deep(.renderedHtml > p) {
  padding-top: 10px;
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

:deep(.renderedHtml > p > img) {
  padding: 10px;
  max-width: 300px; /* Set the maximum width */
  height: auto; /* Maintains aspect ratio */
}

</style>
