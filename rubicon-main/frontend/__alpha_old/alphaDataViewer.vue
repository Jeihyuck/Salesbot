<template>
  <v-container>
    <template  v-for="item in viewModel">
      <v-col :cols="12" :key="item.title" class="d-flex align-center py-1">
        <v-row v-if="item.type === 'text'" class="py-2">
          <p :style="flexTitle" class="text-subtitle-2 primary--text font-weight-bold mb-0">{{ item.title }}</p>
          <p class="text-subtitle-2 primary--text font-weight-bold mb-0 mr-4">:</p>
          <p :style="flexValue" v-if="!edit" class="black--text mb-0">{{ item.value }}</p>
          <alpha-text-input-field
            v-if="item.type === 'text' && edit"
            v-model="item.value"
            >
          </alpha-text-input-field>
        </v-row>
        <!-- <v-row v-if="item.type === 'divider'" class="py-3">

        </v-row> -->
        <v-row v-if="item.type === 'title'" class="text-caption pt-3">
          <v-col class="px-0 mx-0">
            <div>{{item.value}}</div>
            <v-divider class="mt-1 mb-2"></v-divider>
          </v-col>
        </v-row>
        <v-row v-if="item.type === 'base64Image'" class="py-3">
          <p :style="flexTitle" class="text-subtitle-2 primary--text font-weight-bold mb-0">{{ item.title }}</p>
          <p class="text-subtitle-2 primary--text font-weight-bold mb-0 mr-4">:</p>
          <img :src="getBase64Image(item.value)" width="500" height="500"/>
        </v-row>
        <v-row v-if="item.type === 'pdf'" class="py-3">
          <v-col class="mx-0 px-0">
          <p class="text-subtitle-2 primary--text font-weight-bold mb-4">{{ filename(item) }}</p>
          <alpha-p-d-f-viewer
            :url="item.url"
          />
          </v-col>
        </v-row>
      </v-col>
    </template>
  </v-container>
</template>

<script>
import alphaPDFViewer from '@/components/alpha/alphaPDFViewer'
import alphaTextInputField from '@/components/alpha/alphaTextInputField'

export default {
  name: 'alphaDataViewer',
  components: { alphaPDFViewer, alphaTextInputField },
  props: {
    width: {
      type: [Number, String],
      default: '10vw'
    },
    id: String,
    edit: Boolean,
    dialogVisible: {
      type: Boolean,
      default: false
    },
    viewModel: Array
  },
  computed: {
    flexTitle: {
      get () {
        return {
          flex: `0 0 ${typeof this.width === 'number' ? this.width + 'px' : this.width}` // might be fixed later
        }
      }
    },
    fileTitle: {
      get () {
        return {
          flex: `0 0 ${typeof this.width === 'number' ? '500px' : 500}` // might be fixed later
        }
      }
    },
    flexValue: {
      get () {
        return {
          flex: '1 1'
        }
      }
    }
  },
  // watch: {
  //   dialogVisible: function () {
  //     console.log(this.dialogVisible)
  //     console.log('Dataview Dialog Visible')
  //     if (this.dialogVisible === true) {
  //       this.$nextTick(function () {
  //         this.getPDFFile()
  //       })
  //     }
  //   }
  // },
  methods: {
    filename (item) {
      const filename = item.title
      return filename
    },
    getPDFFile () {
      for (let i = 0; i < this.viewModel.length; i++) {
        if (this.viewModel[i].type === 'pdf') {
          this.$alpha.getFileURL(this.viewModel[i].storage, this.viewModel[i].path, this.viewModel[i].filename).then(fileURL => {
            this.$set(this.viewModel[i], 'url', fileURL)
          })
        }
      }
    },
    getBase64Image (base64) {
      return 'data:image/png;base64,' + base64
    }
  }
  // mounted () {
  //   this.$nextTick(function () {
  //     this.getPDFFile()
  //   })
  // }
}
</script>

<style lang="sass" scoped>
  .card--text
    word-break: break-all !important
</style>
