<template>
  <v-dialog v-model="dialogVisible" persistent max-width="1200px">
    <template v-slot:activator="{ on, attrs }">
      <v-col class="mt-4 px-2">
        <v-btn small color="white" :on="on" :bind="attrs" @click="showDialog()" outlined block>Prompt Engineering</v-btn>
      </v-col>
    </template>
    <v-card>
      <v-card-title
        class="primary white--text py-1 px-4 text-h6 font-weight-bold"
      >
        Prompt Engineering
      </v-card-title>
      <v-card-text class="pt-0 pb-0 px-1">
        <v-container>
          <v-row class="pb-1">
            <v-col cols="1" class="font-weight-bold">Current Prompt</v-col>
            <!-- <v-col cols="11" class="font-weight-bold">{{doc._id}}</v-col> -->
          </v-row>
          <v-row>
            <v-col cols="12">
              <v-textarea background-color="#1E1E1E" class="custom-textarea font-weight-bold" filled v-model="editingPrompt" auto-grow outlined counter></v-textarea>
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>
      <v-card-actions class="pt-0 pr-4 pb-4">
        <v-spacer></v-spacer>
        <slot name="custom-button"></slot>
        <v-btn
          small
          color="primary"
          outlined
          @click="updatePrompt"
        >
          Update
        </v-btn>
        <!-- <v-btn
          small
          color="primary"
          outlined
          @click="deleteText"
        >
          Delete
        </v-btn> -->
        <v-btn
          small
          color="primary"
          outlined
          @click="cancel"
        >
          Cancel
        </v-btn>
      </v-card-actions>
    </v-card>

  </v-dialog>
</template>

<script>
import { template, getDatetimeStringFromString } from '@/_helpers'

export default {
  props: [
    'prompt'
  ],
  // components: { codemirror },
  data () {
    return {
      dialogVisible: false,
      dialogKey: 0,
      editingPrompt: ''
    }
  },
  computed: {
    btnValue () {
      if (this.editType === 'CREATE') {
        return `New ${this.alphaModel.name}`
      } else {
        return `${this.editType}`
      }
    }
  },
  methods: {
    qualityConfirmed () {
      console.log('qualityConfirmed')
      console.log(this.source, this.doc)
    },
    updatePrompt () {
      console.log('updatePrompt')
      // console.log(this.source, this.doc)
      this.$emit('updatePrompt', this.editingPrompt)
      this.dialogVisible = false
    },
    deleteText () {
      console.log('deleteText')
      console.log(this.source, this.doc)
    },
    cancel () {
      this.dialogVisible = false
      this.$emit('cancel')
    },
    showDialog () {
      // console.log('show Dialog')
      this.dialogKey += 1
      this.dialogVisible = true
      this.$emit('showDialogValues', this.editType)
    },
    getDatetimeString (date) {
      return getDatetimeStringFromString(date)
    },
    getYN (value) {
      if (value === true) {
        return 'Copied'
      } else {
        return 'Not Yet'
      }
    }
  },
  mounted () {
    this.editingPrompt = this.prompt
  }
}
</script>
