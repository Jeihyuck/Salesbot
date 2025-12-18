<template>
  <v-dialog v-model="dialogVisible" persistent :max-width="alphaModel.dialogWidth? alphaModel.dialogWidth:'600px'">
    <template v-slot:activator="{ on, attrs }">
      <alpha-btn :on="on" style="margin: 0px 0px 1px 0px" :bind="attrs" :outlined="editType === 'EDIT' ? true : false" :x-small="editType === 'EDIT' ? true : false" :small="editType === 'CREATE' ? true : false" :color="'primary'" :value="btnValue" :minimize="editType === 'EDIT' ? true : false" @click="showDialog()"></alpha-btn>
    </template>
    <alphaDataTable-dialog
      :editType="editType"
      :alphaModel="alphaModel"
      @update="update"
      @cancel="cancel"
      :key="dialogKey"
    >
      <template v-slot:custom="{ slotName }">
        <slot name="custom" :slotName="slotName"></slot>
      </template>
    </alphaDataTable-dialog>
  </v-dialog>
</template>

<script>
import alphaDataTableDialog from '@/components/alpha/alphaDataTableDialog.vue'
import alphaDataTableDialogWrapperPlugIn from '@/plugins/alphaDataTableDialogWrapper.plugin.js'

export default {
  components: { alphaDataTableDialog },
  props: [
    'editType',
    'alphaModel'
  ],
  data () {
    return {
      dialogVisible: false,
      dialogKey: 0
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
    update () {
      this.$emit('update', this.editType)
    },
    cancel () {
      this.dialogVisible = false
      this.$emit('cancel')
    },
    showDialog () {
      // console.log('show Dialog')
      this.dialogKey += 1
      this.$emit('showDialogValues', this.editType)
    }
    // alphaDataTableDialogHide () {
    //   this.cancel()
    // }
  },
  beforeMount () {
    alphaDataTableDialogWrapperPlugIn.EventBus.$on('cancel', () => {
      this.cancel()
    })
  }
}
</script>
