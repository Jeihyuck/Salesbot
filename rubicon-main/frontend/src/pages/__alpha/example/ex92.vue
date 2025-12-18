<template>
  <v-container fluid class="pa-4 ma-0" :style="{ background: $vuetify.theme.themes.light.background }">
      <ul>
        <li v-for="file in files" :key="file.id">
          <span>{{file.name}}</span> -
          <span>{{file.size}}</span> -
          <span v-if="file.error">{{file.error}}</span>
          <span v-else-if="file.success">success</span>
          <span v-else-if="file.active">active</span>
          <span v-else-if="!!file.error">{{file.error}}</span>
          <span v-else></span>
        </li>
      </ul>

      <v-row>
        <file-upload
          extensions="gif,jpg,jpeg,png,webp"
          accept="image/png,image/gif,image/jpeg,image/webp"
          :multiple="true"
          :size="1024 * 1024 * 10"
          v-model="files"
          @input-filter="inputFilter"
          @input-file="inputFile"
          ref="upload">
        </file-upload>
        <input type="file" ref="fileSelect" style="display: none" accept=".png" @change="onFileChanged"/>
        <v-btn color="primary" small :loading="upload" @click="selectFile">SELECT FILES</v-btn>
        <!-- <button @click="$refs.fileSelect.click()">open file dialog</button> -->
        <!-- <v-btn color="primary" small class="ml-2" v-if="!upload || !upload.active" @click.prevent="upload.active = true">Upload</v-btn> -->
        <v-btn color="primary" small class="ml-2" v-if="!upload || !upload.active" @click.prevent="fileUpload">Upload</v-btn>
      </v-row>

        <!-- <button type="button" >
          <i class="fa fa-arrow-up" aria-hidden="true"></i>
          Start Upload
        </button>
        <button type="button" v-else @click.prevent="upload.active = false">
          <i class="fa fa-stop" aria-hidden="true"></i>
          Stop Upload
        </button>
      </div>
    </div>
    <div class="pt-5 source-code">
      Source code: <a href="https://github.com/lian-yue/vue-upload-component/blob/master/docs/views/examples/Simple.vue">/docs/views/examples/Simple.vue</a>
    </div> -->

  </v-container>
</template>

<script>
// import {ref} from 'vue'
import FileUpload from 'vue-upload-component'

export default {
  name: 'ex92',
  components: { FileUpload },
  data () {
    return {
      upload: null,
      files: []
    }
  },
  methods: {
    inputFilter (newFile, oldFile, prevent) {
      if (newFile && !oldFile) {
        // Before adding a file
        // Filter system files or hide files
        if (/(\/|^)(Thumbs\.db|desktop\.ini|\..+)$/.test(newFile.name)) {
          return prevent()
        }

        // Filter php html js file
        if (/\.(php5?|html?|jsx?)$/i.test(newFile.name)) {
          return prevent()
        }
      }
    },
    inputFile (newFile, oldFile) {
      if (newFile && !oldFile) {
        // add
        console.log('add', newFile)
      }
      if (newFile && oldFile) {
        // update
        console.log('update', newFile)
      }
      if (!newFile && oldFile) {
        // remove
        console.log('remove', oldFile)
      }
    },
    selectFile () {
      this.isSelecting = true
      window.addEventListener('focus', () => {
        this.isSelecting = false
      }, { once: true })

      this.$refs.fileSelect.click()
    },
    onFileChanged (e) {
      const selectedFile = e.target.files[0]
      this.$refs.upload.add(selectedFile)
    },
    addText () {
      console.log('add file')
    },
    fileUpload () {
      console.log(this.files)
      this.$serviceAlpha.stdPostFunction(
        'api/example/ex92/',
        {
          action: 'fileUpload',
          files: this.files
        }
      ).then(response => {
        console.log(response)
      })
    }
  }
}
</script>
