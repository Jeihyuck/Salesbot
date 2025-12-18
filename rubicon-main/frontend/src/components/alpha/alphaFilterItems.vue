<template>
    <div>
      <v-row>
        <template v-for="filter in alphaModel.filter">

        <!-- Year Month Date -->
          <v-col
            v-if="filter.type === 'date' && filter.level === level"
            :key="filter.index"
            :cols="filter.col"
            class="d-flex align-center ma-0 pl-3 pr-0"
          >
            <v-date-input
              variant="outlined"
              density="compact"
              base-color="grey-darken-1"
              hide-details
              color="primary"
              prepend-icon=""
              prepend-inner-icon="mdi-calendar"
              :label="filter.label"
              v-model="filter.selected"
              multiple="range"
              show-adjacent-months
            ></v-date-input>
          </v-col>

          <!-- Dropdown -->
          <v-col
            v-if="filter.type === 'dropdown' && filter.level === level"
            :key="filter.index"
            :cols="filter.col"
            class="d-flex align-center ma-0 pl-3 pr-0"
          >
            <v-combobox
              variant="outlined"
              density="compact"
              base-color="grey-darken-1"
              hide-details
              :clearable="filter.clearable"
              :multiple="filter.multiple"
              :label="filter.label"
              :items="filter.selector"
              v-model="filter.selected"
            ></v-combobox>
          </v-col>

          <!-- Text -->
          <v-col
            v-if="filter.type === 'text' && filter.level === level"
            :key="filter.index"
            :cols="filter.col"
            class="d-flex align-center ma-0 pl-3 pr-0"
          >
            <v-text-field
              density="compact"
              base-color="grey-darken-1"
              :label="filter.label"
              v-model="filter.selected"
              variant="outlined"
              hide-details
            >
              <!-- <template v-if="dialog.required" v-slot:label>
                {{ dialog.label }}<span class="text-red"><strong> *</strong></span>
              </template> -->
            </v-text-field>
          </v-col>
        </template>
      </v-row>
    </div>
  </template>
<script>
import { VDateInput } from 'vuetify/labs/VDateInput'

export default {
  name: 'alphaFilterItems',
  props: ['alphaModel', 'level'],
  data () {
    return {
    }
  },
  methods: {
    onFilterSet (key, value) {
      this.$emit('update:filter', {
        key: key,
        value: value
      })
    },
    filteringTable () {
      this.$emit('click:filter', this.alphaModel)
    }
  }
}
</script>
