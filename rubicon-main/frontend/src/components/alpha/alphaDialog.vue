<template>
  <v-dialog v-model="dialogVisible" persistent :max-width="alphaModel.dialogWidth? alphaModel.dialogWidth:'600px'">
    <template v-slot:activator="{ props: activatorProps }">
      <v-btn v-bind="activatorProps" :variant="props.editType === 'EDIT' ? 'outlined' : 'tonal'" :color="props.editType === 'EDIT' ? 'primary' : 'default'" :size="props.editType === 'EDIT' ? 'x-small' : 'small'" @click="props.editType === 'EDIT' ? showDialogValues() : initDialogValues()">{{ btnValue }}
        <v-tooltip
          v-if="props.editType === 'EDIT'"
          activator="parent"
          location="top"
          height="24px"
          class="text-primary"
        >Edit</v-tooltip>
      </v-btn>
    </template>
    <template v-slot:default="{ isActive }"> 
      <v-card :title="dialogTitle">
        <v-card-text class="pt-5 pb-2">
          <template v-for="dialog in alphaModel.dialog">
            <!-- For dropdown field -->
            <v-row>
              <v-col
                v-if="dialog.type === 'dropdown'"
                :key="dialog.index"
                class="d-flex align-center"
              >
                <v-combobox
                  variant="outlined"
                  density="compact"
                  base-color="grey-darken-1"
                  hide-details
                  :clearable="dialog.clearable"
                  :multiple="dialog.multiple"
                  :label="dialog.label"
                  :items="dialog.selector"
                  v-model="dialog.selected"
                ></v-combobox>
              </v-col>
            </v-row>

            <!-- For text item -->
            <v-row>
              <v-col
                v-if="dialog.type === 'text'"
                :key="dialog.index"
                class="d-flex align-center"
              >
              <v-text-field
                density="compact"
                base-color="grey-darken-1"
                :label="dialog.label"
                v-model="dialog.selected"
                variant="outlined"
                hide-details
              >
              <template v-if="dialog.required" v-slot:label>
                {{ dialog.label }}<span class="text-red"><strong> *</strong></span>
              </template>
              </v-text-field>
              </v-col>
            </v-row>

            <!-- For text area -->
            <v-row>
              <v-col
                v-if="dialog.type === 'textarea'"
                :key="dialog.index"
              >
              <v-textarea
                density="compact"
                base-color="grey-darken-1"
                :label="dialog.label"
                v-model="dialog.selected"
                variant="outlined"
                hide-details
              ></v-textarea>
              </v-col>
            </v-row>

            <!-- For source -->
            <v-row>
              <v-col
                v-if="dialog.type === 'code'"
                :key="dialog.index"
              >
              <codemirror
                v-model="dialog.selected"
                placeholder="Code goes here..."
                :style="{ borderRadius: '6px', border: '1px solid #444444' }"
                :autofocus="true"
                :lineWrapping="true"
                :indent-with-tab="true"
                :tab-size="2"
                :extensions="getExtensions(dialog.language)"
              />
              </v-col>
            </v-row>
          </template>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            :text="props.editType === 'EDIT' ? 'Update' : 'Create'"
            variant="tonal"
            class="my-2"
            @click="props.editType === 'EDIT' ? update() : create()"
          ></v-btn>
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
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { toRefs } from 'vue'
import { Codemirror } from 'vue-codemirror'
import { EditorView } from "@codemirror/view"
import { markdown } from '@codemirror/lang-markdown'
import { json, jsonParseLinter } from '@codemirror/lang-json'
import { vscodeDark } from '@uiw/codemirror-theme-vscode'
import { linter } from '@codemirror/lint'

// Props
const props = defineProps({
  editType: String,
  alphaModel: Object
})

// Emit events
const emit = defineEmits(['update', 'updateTable', 'cancel', 'showDialogValues'])

// Reactive state
const dialogVisible = ref(false)
const dialogKey = ref(0)


// Computed properties
const btnValue = computed(() => 
  props.editType === 'CREATE' ? `New ${props.alphaModel.itemName}` : `${props.editType[0]}`
)

// const extensions = [markdown(), vscodeDark, EditorView.lineWrapping]

const dialogTitle = computed(() => {
  if (props.editType === 'EDIT') return `Edit ${props.alphaModel.itemName}`
  if (props.editType === 'CREATE') return `New ${props.alphaModel.itemName}`
})

// Methods
// const getLabel = (label, required) => {
//   return required ? `* ${label}` : label;
// }

const getExtensions = (language) => {
  if (language === 'markdown') {
    return [markdown(), vscodeDark, EditorView.lineWrapping]
  } else if (language === 'json') {
    return [json(), vscodeDark, linter(jsonParseLinter()), EditorView.lineWrapping]
  }
}

const create = () => {
  props.alphaModel['createParams'] = { query: {} }

  for (const [key, value] of Object.entries(props.alphaModel.dialog)) {
    if (typeof value.selected === 'object' && value.selected !== null) {
      if ('value' in value.selected) {
        props.alphaModel['createParams'].query[key] = value.selected.value
      } 
    } else {
        props.alphaModel['createParams'].query[key] = value.selected
    }
  }
  dialogVisible.value = false
  props.alphaModel.function('create', props.alphaModel['createParams'].query).then((response) => {
    // dataTable.value.requestTableData(props.alphaModel)
  }).then(() => {
    emit('updateTable')
  })
}


const update = () => {
  emit('update')
  dialogVisible.value = false
}

const cancel = () => {
  dialogVisible.value = false
  emit('cancel')
}

const showDialogValues = () => {
  dialogKey.value += 1
  emit('showDialogValues', props.editType)
}

const initDialogValues = () => {
  dialogKey.value += 1
  for (const [key, value] of Object.entries(props.alphaModel.dialog)) {
    value.selected = null
    if (value.default) {
      value.selected = value.default
    }
  }
}
</script>

