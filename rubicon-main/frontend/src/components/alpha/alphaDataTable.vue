<template>
  <v-row class="pa-0 ma-0">
    <v-data-table-server
      :key="tableKey"
      :loading="loading"
      v-model="selected"
      item-value="id"
      :show-select="alphaModel.showSelect"
      :headers="alphaModel.tableHeader"
      :items="alphaModel.tableData"
      :items-length="totalItemCount"
      :items-per-page="alphaModel.paging.itemsPerPage"
      :header-props="{ class: 'bg-surface-light' }"
      hover
      class="border rounded"
      v-model:options="alphaModel.paging"
      @update:options="requestTableData"
      @click:row="onClickRow"
      density="compact"
    >
    <template v-for="field in alphaModel.customFields" v-slot:[`item.${field}`]="{ item }">
      <slot :name="`${field}_custom`" v-bind:item="item"></slot>
    </template>
    <template v-slot:item.action="{ item }">
      <slot v-bind:item="item" name="table_custom_action"></slot>
      <alphaDataTableDialog
        v-if="alphaModel.crud[2]"
        :editType="`EDIT`"
        :alphaModel="alphaModel"
        @update="update"
        @showDialogValues="showDialogValues($event, item)"
      >
      </alphaDataTableDialog>
      <v-btn v-if="alphaModel.crud[3]" class="ml-1" variant='outlined' size="x-small" :color="'primary'" @click="deleteItem(item.index, item)">D
        <v-tooltip
          activator="parent"
          location="top"
          height="24px"
          class="text-primary"
        >Delete</v-tooltip>
      </v-btn>
    </template>
    </v-data-table-server>
    <alphaConfirm :key="confirmRefreshKey" ref="deleteConfirm" /> 
  </v-row>
</template>

<script setup>
import { ref, defineAsyncComponent } from 'vue'
import { alpha } from '@/_services'
import { addIndexToArray } from '@/_helpers'
import alphaDataTableDialog from '@/components/alpha/alphaDataTableDialog'

const alphaConfirm = defineAsyncComponent(() => import('@/components/alpha/alphaConfirm'))

const { alphaModel } = defineProps({
  alphaModel: Object
})

const emit = defineEmits(['onClickRow'])

const tableHeaderLoaded = ref(false)
const selected = ref([])
const totalItemCount = ref(0)
const loading = ref(true)
const tableKey = ref(1)
const confirmRefreshKey = ref(10000)
const deleteConfirm = ref(null)

watch(
  () => selected,
  (newVal, oldVal) => {
    // console.log(newVal.value)
    alphaModel.selected = newVal.value
  },
  { deep: true }  // Enable deep watching
);


const requestTableData = () => {
  if (alphaModel.headerId !== 'custom-header' && !tableHeaderLoaded.value) {
    requestHeader()
  }
  if (alphaModel.function) {
    requestData()
  }
}

defineExpose({
  requestTableData
})

const update = () => {
  alphaModel['updateParams'] = { query: {} }

  // if (alphaModel.injectedQuery) {
  //   alphaModel['updateParams'].query.injectedQuery = alphaModel.injectedQuery
  // }

  for (const [key, value] of Object.entries(alphaModel.dialog)) {
    // console.log(key, value)
    if (typeof value.selected === 'object' && value.selected !== null) {
      if ('value' in value.selected) {
        alphaModel['updateParams'].query[key] = value.selected.value
      } 
    } else {
        alphaModel['updateParams'].query[key] = value.selected
    }

  }
  // console.log(alphaModel['updateParams'])
  alphaModel.function('update', alphaModel['updateParams'].query).then((response) => {
    // console.log(response)
    requestTableData()
  })
}

const stringifyNestedObjects = (obj) => {
  for (const prop in obj) {
    if (typeof obj[prop] === 'object' && obj[prop] !== null) {
      obj[prop] = JSON.stringify(obj[prop])
    }
  }
  return obj
}


const requestData = () => {
  loading.value = true
  if (alphaModel.paging.fullLoad === undefined) {
    alphaModel.paging.fullLoad = false
  }
  const paging = {
    page: alphaModel.paging.page,
    itemsPerPage: alphaModel.paging.itemsPerPage,
    fullLoad: alphaModel.paging.fullLoad,
  }

  const query = {}
  for (const key in alphaModel.filter) {
    if (alphaModel.filter[key].selected !== undefined && alphaModel.filter[key].selected !== null && alphaModel.filter[key].selected !== '') {
      query[key] = alphaModel.filter[key].selected
    }
  }

  // const query = {}
  // for (const key in alphaModel.filter) {
  //   const filterItem = alphaModel.filter[key]
  //   if (filterItem.selected !== undefined && filterItem.selected !== null) {
  //     if (filterItem.selected.map(item => typeof item === 'object')) {
  //       query[key] = filterItem.selected.map(item => item.value)
  //     } else {
  //       query[key] = filterItem.selected
  //     }
  //   }
  // }
  if (alphaModel.injectedQuery) {
    query.injectedQuery = alphaModel.injectedQuery
  }
  alphaModel.function('read', query, paging).then(response => {
    loading.value = false
    if (response.success && response.data !== null) {

      for (let i = 0; i < response.data.length; i++) {
        response.data[i] = stringifyNestedObjects(response.data[i])
      }

      if (alphaModel.sort) {
        response.data.sort(alphaModel.sort)
      }
      alphaModel.tableData = addIndexToArray(
        response.data,
        (alphaModel.paging.page - 1) * alphaModel.paging.itemsPerPage + 1
      )
      if (response.meta[0]) {
        totalItemCount.value = response.meta[0].itemCount
      }
    }
  })
}

const requestHeader = () => {
  alpha.table.getTableHeader(alphaModel.headerId).then(response => {
    alphaModel.tableHeader = response.data
    alphaModel.headerField = response.data.map(item => item.value)
    tableHeaderLoaded.value = true
  })
}

async function deleteItem(itemIndex, item) {
  // console.log(item)
  if (
    await deleteConfirm.value.open('Confirm', 'Do you really want to delete?')
  ) {
    alphaModel
      .function('delete', { id: item.id })
      .then(() => {
        confirmRefreshKey.value += 1
        requestTableData()
      })
  }
  // tableKey.value += 1
}

const showDialogValues = (editType, editingRowData) => {
  console.log('showDialogValues on Data Table for EDIT')
  // console.log(editType)
  alphaModel.dialog.id = { selected: editingRowData.id }
  Object.entries(alphaModel.dialog).forEach(([key, value]) => {
    if (Object.keys(editingRowData).includes(key)) {
      if (value.language !== undefined) {
        if (value.language === 'json') {
          value.selected = JSON.stringify(JSON.parse(editingRowData[key]), null, 2)
        } else {
          value.selected = editingRowData[key]
        }
      } else {
        value.selected = editingRowData[key]
      }
    }
  })
  editingRowData = {}
}

function onClickRow(click, row) {
  emit('onClickRow', row)
}

onMounted(() => {
  if (!alphaModel.loading) {
    loading.value = false
  } else {
    loading.value = true
  }
});


</script>
