<template>
  <div>
    <v-row>
      <template v-for="filter in alphaModel.filter">
        <!-- Dropdown -->
        <v-col
          v-if="filter.type === 'dropdown' && filter.level === level"
          :key="filter.index"
          :cols="filter.col"
          class="d-flex align-center ma-0 pl-3 pr-0"
        >
          <alpha-select
            hide-details
            dense
            :prependInnerIcon="getIcon(filter.prependInnerIcon)"
            :clearable="filter.clearable"
            :multiple="filter.multiple"
            :maxDisplay="filter.maxDisplay === undefined ? 2 : filter.maxDisplay"
            :items="filter.selector"
            :label="filter.name"
            v-model="filter.selected"
          />
        </v-col>
        <!-- Year Month Date -->
        <v-col
          v-else-if="filter.type === 'yearMonthDate' && filter.level === level"
          :key="filter.index"
          :cols="filter.col"
          class="ma-0 pl-3 pr-0"
        >
          <alpha-select-calendar-date
            hide-details
            dense
            clearable
            :prependInnerIcon="filter.prependInnerIcon === undefined ? getIcon('mdiCalendarToday') : getIcon(filter.prependInnerIcon)"
            :label="filter.name"
            v-model="filter.selected"
          />
        </v-col>
        <!-- Select Time -->
        <v-col
          v-else-if="filter.type === 'time'  && filter.level === level"
          :key="filter.index"
          :cols="filter.col"
          class="ma-0 pl-3 pr-0"
        >
          <alpha-select-time
            hide-details
            dense
            clearable
            :prependInnerIcon="filter.prependInnerIcon === undefined ? getIcon('mdiClockTimeFourOutline') : getIcon(filter.prependInnerIcon)"
            :label="filter.name"
            v-model="filter.selected"
          />
        </v-col>
        <!-- Year Month Date Time -->
        <v-col
          v-else-if="filter.type === 'yearMonthDateTime' && filter.level === level"
          :key="filter.index"
          :cols="filter.col"
          class="d-flex ma-0 pl-3 pr-0"
        >
        <div class="mr-1">
          <alpha-select-calendar-date
            hide-details
            dense
            clearable
            :prependInnerIcon="getIcon('mdiCalendarToday')"
            :label="filter.name[0]"
            v-model="filter.selected[0]"
          />
        </div>
        <div class="ml-1">
          <alpha-select-time
            hide-details
            dense
            clearable
            :prependInnerIcon="getIcon('mdiClockTimeFourOutline')"
            :label="filter.name[1]"
            v-model="filter.selected[1]"
          />
        </div>
        </v-col>
        <!-- Text -->
        <v-col
          v-else-if="filter.type === 'text' && filter.level === level"
          :key="filter.index"
          :cols="filter.col"
          class="ma-0 pl-3 pr-0"
        >
        <!-- <v-container  fluid >
          <v-row justify="center"> -->
            <alpha-text-field
              class="ma-0 pa-0"
              hide-details="auto"
              :label="filter.name"
              :disabled="filter.disabled"
            ></alpha-text-field>
          <!-- </v-row>
        </v-container> -->
        </v-col>
        <!-- Text Input -->
        <v-col
          v-else-if="filter.type === 'search' && filter.level === level"
          :key="filter.index"
          :cols="filter.col"
          class="ma-0 pl-3 pr-0"
          @keyup.enter="filter.type === 'search' ? filteringTable() : ''"
        >
          <alpha-text-input-field
            :clearable=false
            hide-details="auto"
            :prependInnerIcon="filter.type === 'search' ? getIcon('mdiMagnify') : ''"
            :label="filter.name"
            :disabled="filter.disabled"
            v-model="filter.selected"
          ></alpha-text-input-field>
        </v-col>
        <!-- Autocomplete -->
        <v-col
          v-else-if="filter.type === 'autocomplete' && filter.level === level"
          :key="filter.index"
          :cols="filter.col"
          class="ma-0 pl-3 pr-0"
        >
          <alpha-autocomplete
            hide-details
            clearable
            :multiple="filter.multiple"
            :items="filter.selector"
            :label="filter.name"
            v-model="filter.selected"
          />
        </v-col>
        <!-- filter : Radio -->
        <v-col
          v-if="filter.type === 'radio' && filter.level === level"
          :key="filter.index"
          :cols="filter.col"
          class="ma-0 pl-3 pr-0"
        >
          <v-container class="ma-0 pa-0" fill-height fluid>
          <v-row class="ma-0 pa-0 align-center justify-center fill-height">
            <v-radio-group
              row
              hide-details
              :label="filter.text"
              :disabled="filter.disabled"
              v-model="filter.selected"
              class="ma-0 pa-0"
            >
              <v-radio
                v-for="(selector, i) in filter.selector"
                :key="i"
                :label="selector.text"
                :value="selector.value"
              >
              </v-radio>
            </v-radio-group>
          </v-row>
        </v-container>
        </v-col>
      </template>
    </v-row>
  </div>
</template>

<script>
import { mdiClose, mdiMagnify, mdiCalendarToday, mdiCalendarMonth, mdiCalendarWeek, mdiClockTimeFourOutline } from '@mdi/js'
import alphaSelect from '@/components/alpha/alphaSelect'
import alphaSelectCalendarDate from '@/components/alpha/alphaSelectCalendarDate'
import alphaSelectTime from '@/components/alpha/alphaSelectTime'
// import alphaTextArea from '@/components/alpha/alphaTextArea'
import alphaTextInputField from '@/components/alpha/alphaTextInputField'
import alphaTextField from '@/components/alpha/alphaTextField'
import alphaAutocomplete from '@/components/alpha/alphaAutocomplete'

export default {
  name: 'alphaFilterItems',
  components: { alphaSelect, alphaSelectCalendarDate, alphaSelectTime, alphaTextField, alphaTextInputField, alphaAutocomplete },
  props: ['alphaModel', 'level'],
  data () {
    return {
      icons: {
        mdiMagnify: mdiMagnify,
        mdiCalendarToday: mdiCalendarToday,
        mdiCalendarMonth: mdiCalendarMonth,
        mdiCalendarWeek: mdiCalendarWeek,
        mdiClockTimeFourOutline: mdiClockTimeFourOutline,
        mdiClose: mdiClose
      }
    }
  },
  methods: {
    getIcon (icon) {
      return this.icons[icon]
    },
    onFilterSet (k, v) {
      this.$emit('update:filter', {
        key: k,
        value: v
      })
    },
    filteringTable () {
      this.$emit('click:filter', this.alphaModel)
    }
  }
}
</script>
