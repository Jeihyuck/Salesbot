<template>
  <v-col class="pa-0 ma-0">
    <v-row class="pa-0 ma-0">
    <alphaFilter
        v-if="alphaModel.filter"
        :alphaModel="alphaModel"
        @search="search"
    />
  </v-row>
  <v-row class="d-flex justify-end mx-0 my-2">
    <slot name="table-buttons"></slot>
    <v-btn
      v-if="hasDownload"
      variant="tonal" color="default" size="small"
      style="margin: 0px 0px 1px 0px"
      @click="excelDownload()"
    >Excel Download</v-btn>
    <alphaDataTableDialog
      v-if="alphaModel.crud[0]"
      x-small
      :editType="`CREATE`"
      :alphaModel="alphaModel"
      @updateTable="search"
      >
    </alphaDataTableDialog>
  </v-row>
  <v-row class="pa-0 ma-0">
    <alphaDataTable
      ref="refAlphaDataTable"
      @onClickRow="onClickRow"
      :alphaModel="alphaModel"
    >
      <template v-for="field in alphaModel.customFields" v-slot:[`${field}_custom`]="{ item }">
        <slot :name="`${field}_custom`" v-bind:item="item" />
      </template>
      <template v-slot:table_custom_action="{ item }">
        <slot name="table_custom_action" :item="item"></slot>
      </template>
    </alphaDataTable>
  </v-row>
  </v-col>
</template>

<script setup>
import { ref } from 'vue'
import alphaFilter from '@/components/alpha/alphaFilter.vue'
import alphaDataTable from '@/components/alpha/alphaDataTable.vue'
import alphaDataTableDialog from '@/components/alpha/alphaDataTableDialog.vue'
import { alpha } from '@/_services'
import { v4 as uuidv4 } from 'uuid';
import { serviceAlpha } from '@/_services/index'
// Props
const props = defineProps({
  alphaModel: Object
})

// Emits
const emit = defineEmits(['search', 'onClickRow'])

// Refs
// const refAlphaDataTable = useTemplateRef('refAlphaDataTable')
const refAlphaDataTable = ref(null)
// defineExpose({ dataTable })
// Methods

const search = () => {
  refAlphaDataTable.value.requestTableData()
  emit('search')
}

const onClickRow = (row) => {
  emit('onClickRow', row)
  // this.$emit('onClickRow', row)
}

const hasDownload = computed(() => {
  if (props.alphaModel.excel !== undefined) {
    if (props.alphaModel.excel.download !== undefined) {
      return true
    } else {
      return false
    }
  } else {
    return false
  }
})

const excelDownload = () => {
  const query = {}
  const jobUUID = uuidv4()

  for (const key in props.alphaModel.filter) {
    if (props.alphaModel.filter[key].selected !== undefined && props.alphaModel.filter[key].selected !== null && props.alphaModel.filter[key].selected !== '') {
      query[key] = props.alphaModel.filter[key].selected
    }
  }

  alpha.util.excelDownload(
    jobUUID,
    props.alphaModel.excel.download.fuctionUrl,
    props.alphaModel.excel.download.action,
    query,
    props.alphaModel.excel.download.template
  ).then(() => {
    const fileName = jobUUID + '.xlsx'
    
    serviceAlpha.getFile(fileName, props.alphaModel.excel.download.filename)
  })
}

defineExpose({
  search
})


</script>

