<template>
  <v-dialog
    v-model="dialog"
    :max-width="options.width"
    :style="{ zIndex: options.zIndex }"
    @keydown.esc="cancel"
  >
    <v-card>
      <v-card-title class="primary white--text pt-4 px-8 text-h6 font-weight-bold">
        {{ title }}
      </v-card-title>
      <v-card-text
        v-show="!!message"
        class="pl-8 pt-2 black--text"
        v-html="message"
      ></v-card-text>
      <v-card-actions class="pt-0 pr-4 pb-3">
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          small
          @click.native="agree"
          >OK</v-btn
        >
        <v-btn
          v-if="!options.noconfirm"
          color="primary"
          small
          outlined
          @click.native="cancel"
          >Cancel</v-btn
        >
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'alphaConfirm',
  data () {
    return {
      dialog: false,
      resolve: null,
      reject: null,
      message: null,
      title: null,
      options: {
        color: 'grey lighten-3',
        width: 400,
        zIndex: 200,
        noconfirm: false
      }
    }
  },
  methods: {
    open (title, message, options) {
      this.dialog = true
      this.title = title
      this.message = message
      this.options = Object.assign(this.options, options)
      return new Promise((resolve, reject) => {
        this.resolve = resolve
        this.reject = reject
      })
    },
    agree () {
      this.resolve(true)
      this.dialog = false
    },
    cancel () {
      this.resolve(false)
      this.dialog = false
    }
  }
}
</script>
