<template>
  <v-dialog v-model="dialogVisible" persistent :max-width="alphaModel.dialog.width? getDialogWidth:'600px'">
    <template v-slot:activator="{ on, attrs }">
      <!-- <alpha-btn :on="on" style="margin: 0px 0px 1px 0px" :bind="attrs" small color="primary" :value="alphaModel.dialog.btnText" @click="showDialog()"></alpha-btn> -->
      <alpha-btn :on="on" class="ml-2" :bind="attrs" small color="primary" :value="alphaModel.dialog.btnText" @click="showDialog()"></alpha-btn>
    </template>
    <alpha-dialog
      :alphaModel="alphaModel"
      @update="update"
      @cancel="cancel"
      :key="dialogKey"
    >
      <template v-slot:table_custom_action="{ item }">
        <slot name="table_custom_action" :item="item"></slot>
      </template>
      <template v-slot:custom>
        <slot name="custom"></slot>
      </template>
      <template v-slot:custom-button>
        <slot name="custom-button"></slot>
      </template>
    </alpha-dialog>
  </v-dialog>
</template>

<script>
import alphaDialog from '@/components/alpha/alphaDialog.vue'

export default {
  components: { alphaDialog },
  props: [
    'alphaModel'
  ],
  data () {
    return {
      dialogVisible: false,
      dialogKey: 0
    }
  },
  computed: {
    getDialogWidth () {
      const width = String(this.alphaModel.dialog.width * 200) + 'px'
      console.log(width)
      return width
    }
  },
  methods: {
    update () {
      this.$emit('update')
    },
    cancel () {
      // console.log('cancel')
      this.dialogVisible = false
      this.$emit('cancel')
    },
    showDialog () {
      this.dialogKey += 1
      this.$emit('showDialogValues')
    }
  }
}
</script>
