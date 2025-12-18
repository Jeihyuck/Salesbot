<template>
  <v-card>
    <v-card-title
      v-if="editType === 'CREATE'"
      class="primary white--text py-1 px-4 text-h6 font-weight-bold"
    >
      New {{ alphaModel.name }}
    </v-card-title>
    <v-card-title
      v-else-if="editType === 'EDIT'"
      class="primary white--text py-1 px-4 text-h6 font-weight-bold"
    >
      Edit {{ alphaModel.name }}
    </v-card-title>
    <v-card-title
      v-else
      class="primary white--text py-1 px-4 text-h6 font-weight-bold"
    >
      {{ capitalizeFirstLetter(editType) }} {{ alphaModel.name }}
    </v-card-title>
    <v-card-text class="pt-0 pb-0 px-1">
      <v-container>
        <template v-for="dialog in alphaModel.dialog">
          <!-- dropdown -->
          <v-col
            v-if="dialog.type === 'dropdown' && !(dialog.hide && dialog.hide(editType))"
            :key="dialog.name"
            class="pt-3 pb-1"
          >
            <alpha-select
              dense
              :multiple="dialog.multiple"
              :items="dialog.selector"
              :label="dialog.name"
              :disabled="dialog.disabled(editType)"
              :class="{ 'font-weight-bold': dialog.disabled(editType) }"
              v-model="dialog.selected"
            >
              <template v-if="dialog.required" v-slot:label>
                <span><strong class="red--text">* </strong></span
                >{{ dialog.name }}
              </template>
            </alpha-select>
          </v-col>

          <!-- input -->
          <v-col
            v-else-if="dialog.type === 'input' && !(dialog.hide && dialog.hide(editType))"
            :key="dialog.name"
            class="pt-3 pb-1"
          >
          <!-- :is-strict-number="dialog.isStrictNumber"
              :strict-number-options="dialog.strictNumberOptions" -->
            <alpha-text-input-field
              :label="dialog.name"
              v-model="dialog.selected"
              :type="dialog.number ? 'number' : 'text'"
              :disabled="dialog.disabled(editType)"
              :class="{ 'font-weight-bold': dialog.disabled(editType) }"
              ><template v-if="dialog.required" v-slot:label>
                <span class="red--text"><strong>* </strong></span
                >{{ dialog.name }}
              </template>
            </alpha-text-input-field>
          </v-col>

          <v-col
            v-else-if="dialog.type === 'textarea' && !(dialog.hide)"
            :key="dialog.name"
            class="pt-3 pb-1"
          >
            <alpha-text-area
              :label="dialog.name"
              v-model="dialog.selected"
              ><template v-if="dialog.required" v-slot:label>
                <span class="red--text"><strong>* </strong></span
                >{{ dialog.name }}
              </template>
            </alpha-text-area>
          </v-col>

          <!-- autocomplete -->
          <v-col
            v-else-if="
              dialog.type === 'autocomplete' && !(dialog.hide && dialog.hide(editType))
            "
            :key="dialog.name"
            class="pt-3 pb-1"
          >
            <alpha-autocomplete
              :multiple="dialog.multiple"
              :items="dialog.selector"
              :label="dialog.name"
              v-model="dialog.selected"
            >
              <template v-if="dialog.required" v-slot:label>
                <span class="red--text"><strong>* </strong></span
                >{{ dialog.name }}
              </template>
            </alpha-autocomplete>
          </v-col>

          <!-- combobox -->
          <!-- <v-col
            v-if="dialog.type === 'combobox' && !(dialog.hide && dialog.hide(editType))"
            :key="dialog.name"
            class="pt-3 pb-1"
          >
            <alpha-combobox
              :multiple="dialog.multiple"
              :items="dialog.selector"
              :label="dialog.name"
              :disabled="dialog.disabled(editType)"
              :class="{ 'font-weight-bold': dialog.disabled(editType) }"
              v-model="dialog.selected"
            >
              <template v-if="dialog.required" v-slot:label>
                <span class="red--text"><strong>* </strong></span
                >{{ dialog.name }}
              </template>
            </alpha-combobox>
          </v-col> -->

          <!-- datepicker -->
          <v-col
            v-if="dialog.type === 'datepicker' && !(dialog.hide && dialog.hide(editType))"
            :key="dialog.name"
            class="py-0"
          >
            <alpha-select-calendar-date
              :label="dialog.name"
              v-model="dialog.selected"
              :required="dialog.required"
              :disabled="dialog.disabled(editType)"
            />
          </v-col>

          <!-- checkbox -->
          <v-col
            v-if="dialog.type === 'checkbox' && !(dialog.hide && dialog.hide(editType))"
            :key="dialog.name"
            class="py-0"
          >
            <v-checkbox
              :disabled="dialog.disabled(editType)"
              :class="{ 'font-weight-bold': dialog.disabled(editType) }"
              :label="dialog.name"
              v-model=dialog.selected
            >
              <template v-if="dialog.required" v-slot:label>
                <span class="red--text"><strong>*&nbsp;</strong></span>
                {{ dialog.name }}
              </template>
            </v-checkbox>
          </v-col>

          <!-- code -->
          <v-col
            v-if="dialog.type === 'code' && !(dialog.hide && dialog.hide(editType))"
            :key="dialog.name"
            class="pt-2 pb-1"
          >
            <div style="font-size: 0.9em; margin-bottom: -2px;">{{ dialog.name }}</div>

            <v-row class="pa-0 mx-0" style="min-height: 120px;">
              <codemirror v-model="dialog.selected" :options="dialog.language === 'json' ? javascriptOption : pythonOption"></codemirror>
              <!-- <codemirror v-model="dialog.selected" :options="javascriptOption"></codemirror> -->
            </v-row>
          </v-col>

          <!-- group -->
          <v-col
            v-if="dialog.type === 'group' && !(dialog.hide && dialog.hide(editType))"
            :key="dialog.name"
            class="py-0"
          >
            <v-item-group
              :multiple="dialog.multiple"
              v-model="dialog.selected"
            >
              <template class="py-0 mb-0">
                <span v-if="dialog.required" class="red--text"
                  ><strong>* </strong></span
                >{{ dialog.name }}
              </template>

              <v-row>
                <v-col v-for="(item, i) in dialog.selector" :key="i" cols="4">
                  <v-item v-slot="{ active, toggle }" :value="item">
                    <v-card
                      :color="active ? 'accent' : ''"
                      :dark="!!active"
                      primary
                      height="50"
                      class="text-center pa-2"
                      @click="toggle"
                    >
                      {{ item }}
                      <v-btn icon>
                        <v-icon>
                          {{ active ? 'mdi-heart' : 'mdi-heart-outline' }}
                        </v-icon>
                      </v-btn>
                    </v-card>
                  </v-item>
                </v-col>
              </v-row>
            </v-item-group>
          </v-col>

          <!-- custom -->
          <v-col
            v-if="dialog.type === 'custom' && !(dialog.hide && dialog.hide(editType))"
            :key="dialog.name"
            class="py-0"
          >
            <slot name="custom" :slotName="dialog.name"></slot>
          </v-col>
        </template>
      </v-container>
    </v-card-text>
    <v-card-actions class="pt-0 pr-4 pb-4">
      <v-spacer></v-spacer>
      <v-btn
        v-if="editType === 'CREATE'"
        small
        color="primary"
        @click="update"
      >
        Create
      </v-btn>
      <v-btn
        v-else-if="editType === 'EDIT'"
        small
        color="primary"
        @click="update">
        Update
      </v-btn>
      <v-btn
        v-else
        color="primary"
        outlined
        small
        @click="update"
      >
        {{ capitalizeFirstLetter(editType) }}
      </v-btn>
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
</template>

<script>
import { capitalizeFirstLetter } from '@/_helpers/util'
import alphaTextInputField from '@/components/alpha/alphaTextInputField'
import alphaAutocomplete from '@/components/alpha/alphaAutocomplete'
import alphaSelect from '@/components/alpha/alphaSelect'
// import alphaCombobox from '@/components/alpha/alphaCombobox'
import alphaSelectCalendarDate from '@/components/alpha/alphaSelectCalendarDate'
import alphaTextArea from '@/components/alpha/alphaTextArea'

import { codemirror } from 'vue-codemirror'
import 'codemirror/lib/codemirror.css'

import 'codemirror/mode/javascript/javascript.js'
// import 'codemirror/theme/lesser-dark.css'
import 'codemirror/theme/vscode-dark.css'
// import 'codemirror/theme/github.css'
// require active-line.js
import 'codemirror/addon/selection/active-line.js'

// styleSelectedText
import 'codemirror/addon/selection/mark-selection.js'

// hint
import 'codemirror/addon/hint/show-hint.js'
import 'codemirror/addon/hint/show-hint.css'
import 'codemirror/addon/hint/javascript-hint.js'

// highlightSelectionMatches
import 'codemirror/addon/scroll/annotatescrollbar.js'
import 'codemirror/addon/search/matchesonscrollbar.js'
import 'codemirror/addon/search/match-highlighter.js'

// keyMap
import 'codemirror/mode/clike/clike.js'
import 'codemirror/addon/edit/matchbrackets.js'
import 'codemirror/addon/comment/comment.js'
import 'codemirror/addon/dialog/dialog.js'
import 'codemirror/addon/dialog/dialog.css'
import 'codemirror/addon/search/searchcursor.js'
import 'codemirror/addon/search/search.js'
import 'codemirror/keymap/sublime.js'

// foldGutter
import 'codemirror/addon/fold/foldgutter.css'
import 'codemirror/addon/fold/brace-fold.js'
import 'codemirror/addon/fold/comment-fold.js'
import 'codemirror/addon/fold/foldcode.js'
import 'codemirror/addon/fold/foldgutter.js'
import 'codemirror/addon/fold/indent-fold.js'
import 'codemirror/addon/fold/markdown-fold.js'
import 'codemirror/addon/fold/xml-fold.js'

// this.request = JSON.stringify(response.data.request, null, 2)
// this.response = JSON.stringify(response.data.response, null, 2)

export default {
  name: 'alphaDataTableDialog',
  components: { alphaSelectCalendarDate, alphaSelect, alphaAutocomplete, alphaTextInputField, codemirror, alphaTextArea },
  props: [
    'editType',
    'alphaModel'
  ],
  data () {
    return {
      datePickerHolder: {},
      pythonOption: {
        tabSize: 2,
        styleActiveLine: true,
        // lineNumbers: true,
        line: true,
        // foldGutter: true,
        styleSelectedText: true,
        mode: 'text/x-python',
        theme: 'vscode-dark',
        keyMap: 'sublime',
        matchBrackets: true,
        showCursorWhenSelecting: true,
        extraKeys: { Ctrl: 'autocomplete' },
        // gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter'],
        hintOptions: {
          completeSingle: false
        }
      },
      javascriptOption: {
        tabSize: 2,
        styleActiveLine: true,
        // lineNumbers: true,
        // line: true,
        // foldGutter: true,
        styleSelectedText: true,
        mode: {
          name: 'javascript',
          json: true,
          statementIndent: 2
        },
        theme: 'vscode-dark',
        keyMap: 'sublime',
        matchBrackets: true,
        showCursorWhenSelecting: true,
        extraKeys: { Ctrl: 'autocomplete' },
        // gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter'],
        hintOptions: {
          completeSingle: false
        }
      }
    }
  },
  methods: {
    capitalizeFirstLetter: capitalizeFirstLetter,
    update () {
      this.$emit('update', this.alphaModel)
    },
    cancel () {
      this.$emit('cancel', this.alphaModel)
    }
    // getCodemirrorOption (language) {
    //   if (language === 'python') {
    //     return pythonOption
    //   } else if (language === 'javascript') {
    //     return javascriptOption
    //   }
    // }
  },
  mounted () {
    for (const key in this.alphaModel.dialog) {
      if (this.alphaModel.dialog[key].type === 'checkbox') {
        if (this.alphaModel.dialog[key].selected === 'Y') {
          this.alphaModel.dialog[key].selected = true
        }
        if (this.alphaModel.dialog[key].selected === '-') {
          this.alphaModel.dialog[key].selected = false
        }
      }
    }
  }
}
</script>

<style scoped>
.vue-codemirror {
  max-height: 120px !important;
  height: 120px !important;
}
</style>
