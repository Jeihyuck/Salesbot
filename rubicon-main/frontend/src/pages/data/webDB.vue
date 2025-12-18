<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <alphaDataTable-view :alphaModel="alphaModel">
      <template v-slot:active_custom="{ item }">
        <div> {{ item.active? 'Y':'-' }}</div>
      </template>
        <template v-slot:table-buttons="{ item }">
          <v-dialog max-width="1200" :key='referenceDialog' v-model="referenceDialogVisible">
            <template v-slot:activator="{ props: activatorProps }">
              <v-btn v-bind="activatorProps" variant="tonal" color="default" size="small" class="ml-2"> Create Reference Data</v-btn>
            </template>
            <template v-slot:default="{ isActive }">
              <v-card  title="Reference Data Creation" class="pa-4">
                <v-card-text class="pb-0">
                  <v-row class="ml-1"> 데이터 생성에 1, 2 분 정도 소요될 수 있습니다. 완료될 때까지 다른 키를 누르지 마세요.</v-row>
                  <v-row class="mt-6">
                    <v-col cols="4">
                      <v-combobox
                        variant="outlined"
                        density="compact"
                        base-color="grey-darken-1"
                        hide-details
                        label="Country Code"
                        :items="['KR', 'GB']"
                        v-model="referenceDialogCountryCode"
                      ></v-combobox>
                    </v-col>
                    <v-col cols="8">
                      <v-text-field
                        v-model="referenceDialogUpdateTag"
                        variant="outlined"
                        density="compact"
                        base-color="grey-darken-1"
                        hide-details
                        label="Created / Updated By"
                      ></v-text-field>
                    </v-col>
                  </v-row>

                  <v-textarea
                    v-model="referenceQuery"
                    variant="outlined"
                    density="compact"
                    base-color="grey-darken-1"
                    hide-details
                    class="mt-4"
                    label="Write your reference query"
                  ></v-textarea>
                </v-card-text>

                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn
                    text="Create"
                    variant="tonal"
                    class="mr-4 my-4"
                    @click="createReference()"
                  ></v-btn>
                  <v-overlay
                    :model-value="creatingReferenceResponse"
                    class="align-center justify-center"
                  >
                    <v-progress-circular
                      color="primary"
                      size="64"
                      indeterminate
                    ></v-progress-circular>
                  </v-overlay>
                  <v-btn
                    text="Cancel"
                    variant="tonal"
                    class="mr-4 my-4"
                    @click="cancel()"
                  ></v-btn>
                </v-card-actions>
              </v-card>
            </template>
          </v-dialog>
          <v-btn variant="tonal" color="default" size="small" class="ml-2" @click="textScrap()">Temp Test</v-btn>
        </template>

    </alphaDataTable-view>

  </v-col>
</template>

<script setup>
import axios from 'axios'
import { ref, reactive } from 'vue'
import { rubiconAdmin } from '@/_services'
import alphaDataTableView from '@/components/alpha/alphaDataTableView.vue'

const creatingReferenceResponse = ref(false)
const referenceDialogVisible = ref(false)
const referenceDialog = ref('1')
const referenceQuery = ref('')
const referenceDialogCountryCode = ref('KR')
const referenceDialogUpdateTag = ref('')
const { proxy } = getCurrentInstance()

const alphaModel = reactive({
  tableUniqueID: 'webDB',
  itemName: 'Web DB',
  paging: { page: 1, itemsPerPage: 15 },
  function: rubiconAdmin.webCache.table,
  crud: [true, true, true, true],
  headerId: '7652b0c8-807a-4f70-91da-9cf5d34ea00e',
  customFields: ["active"],
  filter: {
    hideBoarder: false,
    active: {
      label: 'Active',
      type: 'dropdown',
      clearable: true,
      selector: [true, false],
      selected: null,
      level: 2,
      col: 2
    },
    country_code: {
      label: 'Country',
      type: 'dropdown',
      clearable: true,
      selector: ['KR', 'GB'],
      selected: null,
      level: 2,
      col: 2
    },
    source: {
      label: 'Source',
      type: 'dropdown',
      clearable: true,
      selector: ['web', 'reference', 'graph_db'],
      selected: null,
      level: 2,
      col: 2
    },
    update_tag: {
      label: 'Update Tag',
      type: 'dropdown',
      clearable: true,
      selector: [],
      selected: null,
      level: 2,
      col: 2
    },
    search_word_in_title: {
      label: 'Search Word in Title',
      type: 'text',
      selected: null,
      col: 3
    },
    search_word_in_content: {
      label: 'Search Word in RAG Content',
      type: 'text',
      selected: null,
      col: 3
    },
    embedding_query: {
      label: 'Embedding Query',
      type: 'text',
      selected: null,
      col: 3
    }
  },
  dialogWidth: '1200px',
  dialog: {
    active: {
      label: 'Active',
      type: 'dropdown',
      required: true,
      selector: [true, false],
      selected: null,
    },
    country_code: {
      label: 'Country',
      type: 'dropdown',
      selector: ['KR', 'GB'],
      selected: null,
    },
    title: {
      label: 'Title',
      type: 'text',
      required: true,
      selected: ''
    },
    summary: {
      type: 'code',
      label: 'Embedding Query',
      language: 'markdown',
      selected: ''
    },
    clean_content: {
      type: 'code',
      label: 'RAG Content',
      language: 'markdown',
      selected: ''
    },
    source: {
      label: 'Source',
      type: 'dropdown',
      selector: ['web', 'reference'],
      selected: null,
    },
    update_tag: {
      label: 'Update Tag',
      required: true,
      type: 'text',
      clearable: true,
      selected: null
    },
  }
})

function cancel() {
  referenceDialogVisible.value = false
}

function createReference() {
  if (referenceDialogUpdateTag.value === '') {
    // alert('Please enter the "Created / Updated By" field.')
    
    proxy.$snackbar.showSnackbar({
      title: 'Backend Error',
      message: 'Please enter the "Created / Updated By" field.',
      color: 'error',
      timeout: 2000,
    }) 

    return
  } else {
    creatingReferenceResponse.value = true
    const query = {
      reference_query: referenceQuery.value,
      country_code: referenceDialogCountryCode.value,
      update_tag: referenceDialogUpdateTag.value
    }
    rubiconAdmin.webCache.table('createReferenceRag', query).then(() => {
      referenceDialogVisible.value = false
      referenceQuery.value = ''
      creatingReferenceResponse.value = false
    }).catch((error) => {
      console.error('Error creating Reference data:', error)
    })
  }

}


function textScrap() {
  const params = {
    test: 'test',
  }
  const   axiosConfig = {
    headers: {
      'Content-Type': 'multipart/form-data',
      Authorization: 'accessToken'
    }
  }

  axios.post('http://13.124.66.126/api/web/text_scrap/', params, axiosConfig)
    .then(response => {
      console.log('Text scrap response:', response.data);
    })
}

onMounted(() => {
  const query = {
    country_code: alphaModel.filter.country_code.selected,
  }
  rubiconAdmin.webCache.table('listUpdateTag', query).then((response)=> {
    alphaModel.filter.update_tag.selector = response.data
  })

});
  
</script>
