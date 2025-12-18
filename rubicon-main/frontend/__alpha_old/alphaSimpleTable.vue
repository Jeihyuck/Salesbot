<template>
  <div>
  <v-simple-table
    dense
    v-model="selected"
    :headers="headers"
    :items="tableData"
    :loading="loading"
    item-key="index"
    class="elevation-1 alphaDataTable"
    @click:row="onClickRow"
  >
  </v-simple-table>
  </div>
</template>

<script>
export default {
  name: 'alphaSimpleTable',
  components: {
  },
  data () {
    return {
      query: {},
      selected: [],
      loading: false,
      tableData: [],
      headers: [],
      deleteList: [],
      clickDelete: false
    }
  },
  props: [
    'alphaModel',
    'dialogVisible'
  ],
  watch: {
    selected: {
      deep: true,
      handler () {
        this.$emit('updateTableItemSelected', this.selected)
      }
    }
  },
  created () {
    // this.__handlerRef__ = this.clickOutside.bind(this)
    document.body.addEventListener('click', this.__handlerRef__)
  },
  destroyed () {
    document.body.removeEventListener('click', this.__handlerRef__)
  },
  mounted () {
    this.requestTableData(this.alphaModel)
  },
  methods: {
    requestData (alphaModel) {
      console.log('requestTableData')
    },
    requestTableData (alphaModel, searchByButton = false) {
      console.log('requestTableData')
    },
    onClickRow (row) {
      this.$emit('click:row', row)
    }
  }
}
</script>

<style lang="sass">
  @import '@/alphaColors.scss'
  @import '~@/components/alpha/styles/alphaTextStyles.scss'
</style>
