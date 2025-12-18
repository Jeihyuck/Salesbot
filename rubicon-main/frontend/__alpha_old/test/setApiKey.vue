<template>
  <alpha-dialog-wrapper :alphaModel="setApiKey" ref="dialog">
    <template v-slot:custom-button>
      <v-btn
        small
        color="primary"
        outlined
        @click="saveApiKey"
      >
        OK
      </v-btn>
    </template>
  </alpha-dialog-wrapper>
</template>

<script>
import { alphaTest } from '@/_services'
import alphaDialog from '@/components/alpha/alphaDialog'

export default {
  name: 'setApiKey',
  components: { alphaDialog },
  data () {
    return {
      setApiKey: {
        dialog: {
          btnText: 'Set API Key',
          title: 'Set API Key',
          width: 4,
          type: 'update',
          dialogVisible: false,
          items: [
            {
              type: 'input',
              name: 'API Key',
              selected: ''
            }
          ]
        }
      }
    }
  },
  methods: {
    saveApiKey () {
      // console.log('saveApiKey')
      this.$emit('saveApiKey', this.setApiKey.dialog.items[0].selected)
      this.$refs.dialog.cancel()
    }
  }
}
</script>
