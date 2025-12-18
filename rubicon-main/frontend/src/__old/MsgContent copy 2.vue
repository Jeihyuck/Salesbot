<template>
  <div :class="locationClass" style="width: 100%;">

  <v-card
      :color="isBot ? '#121212':'#2f2f2f'"
      flat style="width: 90%;"
  >
  <v-card-text class="pt-2 pl-4">
    <div v-if="isBot" class="text-caption black--text"> Model : {{ model }}</div>
  </v-card-text>
  <v-card-text class="pt-0 mt-0 pb-0">
    <v-row class="mb-0 pb-0">
      <v-col cols="1" class="mt-n1 mr-n4">
        <v-container class="d-flex align-center justify-end pr-0">
          <v-row class="pb-2 pt-0">
            <img v-if="!isBot" src="@/assets/img/alpha-user.png" style="width: 20px; height: 20px">
            <img v-if="isBot" src="@/assets/img/alpha-chat.png" style="width: 20px; height: 20px">
          </v-row>
        </v-container>
      </v-col>
      <v-col cols="10" class="ml-4 pt-0 ml-0 pl-0 pr-2 pb-0">
        <v-container :class="containerClass">
          <v-row class="pb-3">
            <v-row :class="contextClass" v-html="renderMarkDown(content)"></v-row>
            <v-row v-if="isBot && completed" class="ml-n2 mt-n2 pb-2">
              <v-btn variant="text" size="x-small" icon="mdi-thumb-up-outline" :class="thumbUpClass" @click="thumbUpClick()"></v-btn>
              <v-dialog max-width="600" v-model="dialogVisible">
                <template v-slot:activator="{ props: activatorProps }">
                  <v-btn v-bind="activatorProps" variant="text" size="x-small" icon="mdi-thumb-down-outline" :class="thumbDownClass" @click="thumbDownClick()"></v-btn>
                </template>

                <template v-slot:default="{ isActive }">
                  <v-card title="Please tell me in more detail.">
                    <v-card-text class="pb-0">
                      <v-checkbox density="compact" hide-details
                        v-model="checkList[0]"
                        label="&nbsp;This is Inaccurate"
                      ></v-checkbox>
                      <v-checkbox density="compact" hide-details
                        v-model="checkList[1]"
                        label="&nbsp;This is Irrelevant"
                      ></v-checkbox>
                      <v-checkbox density="compact" hide-details
                        v-model="checkList[2]"
                        label="&nbsp;This is harmful / unsafe"
                      ></v-checkbox>
                      <v-checkbox density="compact" hide-details
                        v-model="checkList[3]"
                        label="&nbsp;This is too slow"
                      ></v-checkbox>
                      <v-checkbox density="compact" hide-details
                        v-model="checkList[4]"
                        label="&nbsp;This is hardly legible."
                      ></v-checkbox>
                      <v-checkbox density="compact" hide-details
                        v-model="checkList[5]"
                        label="&nbsp;Something else"
                      ></v-checkbox>
                      <v-textarea
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
            </v-row>
          </v-row>
        </v-container>
      </v-col>
    </v-row>


  </v-card-text>
  </v-card>
  </div>
</template>

<script>
import { renderMarkDown } from '@/_helpers'
import { compact } from 'lodash';
import { rubicon } from '@/_services'

export default {
  name: 'MsgContent',
  props: {
    content: {
      required: true
    },
    model: {
      required: true
    },
    contentKey: {
      type: Number,
      default: 0
    },
    isBot: {
      type: Boolean,
      required: true
    },
    selectedLLMModel: {
      required: true
    },
    completed: {
      required: true
    },
    messageId: {
      required: true
    },
  },
  data () {
    return {
      thumbUp: false,
      thumbDown: false,
      checkList: [false, false, false, false, false, false],
      comment: '',
      dialogVisible: false
    }
  },
  computed: {
    containerClass: {
      get () {
        if (this.isBot) {
          return 'pr-0'
        } else {
          return 'd-flex align-center pr-0'
        }
      }
      
    },
    contextClass: {
      get () {
        if (this.isBot) {
          return 'markdown-chat pt-0 pb-3'
        } else {
          return 'markdown-chat pt-4 pb-n2'
        }
      }
    },
    locationClass: {
      get () {
        if (this.isBot) {
          return 'd-flex justify-start pa-3'
        } else {
          return 'd-flex justify-end pa-3'
        }
      }
    },
    thumbUpClass: {
      get () {
        if (this.thumbUp) {
          return 'text-primary'
        } else {
          return 'text-grey'
        }
      }
    },
    thumbDownClass: {
      get () {
        if (this.thumbDown) {
          return 'text-primary ml-n1'
        } else {
          return 'text-grey ml-n1'
        }
      }
    },
    cardColor: {
      get () {
        if (this.isBot) {
          if (this.isDebug) {
            return '#444444'
          } else {
            return '#54565F'
          }
        } else {
          return '#343541'
        }
      }
    },
    // allowRun: {
    //   get () {
    //     if (this.selectedGptModel === 'samsung_sql_generator') {
    //       return true
    //     } else {
    //       return false
    //     }
    //   }
    // },
    getContent: {
      get () {
        if (this.content === null) {
          return ''
        } else {
          return this.content
        }
      }
    }
  },
  methods: {
    sendAppraisal () {
      console.log('send appraisal')

      let selection = []
      for (let i = 0; i < this.checkList.length; i++) {
        if (this.checkList[i] === true){
          selection.push(i)
        }
      }


      const query = {
        message_id: this.messageId,
        selection: selection,
        comment: this.comment
      }
      rubicon.appraisal.function ('ut_appraisal', query).then( () =>  {
        this.dialogVisible = false
      })
    },
    cancel () {
      this.dialogVisible = false
    },
    thumbUpClick () {
      this.thumbUp = true
      this.thumbDown = false
    },
    thumbDownClick () {
      this.thumbUp = false
      this.thumbDown = true
    },
    renderMarkDown (text) {
      // console.log(text)
      if (text === null) {
        return renderMarkDown('')
      } else {
        return renderMarkDown(text)
      }
    },
    async copyToClipboard (textToCopy) {
      // Navigator clipboard api needs a secure context (https)
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(textToCopy)
      } else {
        // Use the 'out of viewport hidden text area' trick
        const textArea = document.createElement('textarea')
        textArea.value = textToCopy
        // Move textarea out of the viewport so it's not visible
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
    // handleClick (e) {
    //   // console.log('handle click')
    //   // console.log(e.target.parentElement?.parentElement)
    //   if (e.target.className !== 'copy-action') {
    //     return
    //   }
    //   const content = e.target.parentElement?.parentElement?.parentElement?.querySelector('code')?.innerText || ''
    //   // console.log(content)
    //   // navigator.clipboard.writeText(content)
    //   this.copyToClipboard(content)
    //   this.$notify({
    //     group: 'alpha',
    //     type: 'success',
    //     title: 'Info',
    //     duration: 1000,
    //     text: 'copied to clipboard'
    //   })
    // }
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


</style>
