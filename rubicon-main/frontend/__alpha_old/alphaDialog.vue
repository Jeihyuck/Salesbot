<template>
  <v-card>
    <v-card-title
      class="primary white--text py-1 px-4 text-h6 font-weight-bold"
    >
      {{ alphaModel.dialog.title }}
    </v-card-title>
    <v-card-text class="pt-0 pb-0 px-1">
      <v-container>
        <template v-for="dialog in alphaModel.dialog.items">
          <v-col
            v-if="dialog.type === 'dropdown' && !(dialog.hide)"
            :key="dialog.name"
            class="pt-3 pb-1"
          >
            <alpha-select
              dense
              :multiple="dialog.multiple"
              :items="dialog.selector"
              :label="dialog.name"
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
            v-else-if="dialog.type === 'input' && !(dialog.hide)"
            :key="dialog.name"
            class="pt-3 pb-1"
          >
            <alpha-text-input-field
              :label="dialog.name"
              v-model="dialog.selected"
              :type="dialog.number ? 'number' : 'text'"
              ><template v-if="dialog.required" v-slot:label>
                <span class="red--text"><strong>* </strong></span
                >{{ dialog.name }}
              </template>
            </alpha-text-input-field>
          </v-col>

          <!-- textarea -->
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
              dialog.type === 'autocomplete' && !(dialog.hide)
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

          <!-- datepicker -->
          <v-col
            v-if="dialog.type === 'datepicker' && !(dialog.hide)"
            :key="dialog.name"
            class="py-0"
          >
            <alpha-select-calendar-date
              :label="dialog.name"
              v-model="dialog.selected"
              :required="dialog.required"
            />
          </v-col>

          <!-- checkbox -->
          <v-col
            v-if="dialog.type === 'checkbox' && !(dialog.hide)"
            :key="dialog.name"
            class="py-0"
          >
            <v-checkbox
              :label="dialog.name"
              v-model=dialog.selected
            >
              <template v-if="dialog.required" v-slot:label>
                <span class="red--text"><strong>*&nbsp;</strong></span>
                {{ dialog.name }}
              </template>
            </v-checkbox>
          </v-col>

          <!-- group -->
          <v-col
            v-if="dialog.type === 'group' && !(dialog.hide)"
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

          <!-- dataTable -->
          <v-col
            v-if="dialog.type === 'dataTableView' && !(dialog.hide)"
            :key="dialog.name"
            class="py-0"
          >
          <alphaDataTable-view :alphaModel="dialog.model" class="">
            <template v-slot:table_custom_action="{ item }">
              <slot name="table_custom_action" :item="item"></slot>
            </template>
          </alphaDataTable-view>
          </v-col>

          <!-- custom -->
          <v-col
            v-if="dialog.type === 'custom' && !(dialog.hide)"
            :key="dialog.name"
            class="py-0"
          >
            <slot name="custom"></slot>
          </v-col>
        </template>
      </v-container>
    </v-card-text>
    <v-card-actions class="pt-0 pr-4 pb-4">
      <v-spacer></v-spacer>
      <slot name="custom-button"></slot>
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
import alphaSelectCalendarDate from '@/components/alpha/alphaSelectCalendarDate'
import alphaDataTableView from '@/components/alpha/alphaDataTableView'
import alphaTextArea from '@/components/alpha/alphaTextArea'

export default {
  name: 'alphaDataTableDialog',
  // components: { alphaSelectCalendarDate, alphaSelect, alphaAutocomplete, alphaTextInputField, alphaDataTableView },
  components: { alphaSelectCalendarDate, alphaSelect, alphaAutocomplete, alphaTextInputField, alphaDataTableView, alphaTextArea },
  props: [
    'alphaModel'
  ],
  data () {
    return {
      datePickerHolder: {}
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
