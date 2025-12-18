<template>
  <v-menu ref="selectYearMonth" v-model="selectYearMonth"
    :close-on-content-click="false"
    :return-value.sync="selected"
    transition="scale-transition"
    offset-y max-width="290px" min-width="auto"
  >
    <template v-slot:activator="{ on, attrs }">
      <v-text-field
        flat
        :hide-details="hideDetails"
        :clear-icon="clearIcon"
        :dense="dense"
        :clearable="clearable"
        :label="label"
        :prepend-inner-icon="prependInnerIcon"
        :disabled="disabled"
        readonly
        class="ma-0 pa-0 alpha-text-input-field"
        v-model="selected"
        v-bind="attrs"
        v-on="on"
      >
        <template v-slot:label>
          <slot name="label"></slot>
        </template>
      </v-text-field>
    </template>
    <v-date-picker @change="updateYearMonth(selectedYearMonthDate)" v-model="selectedYearMonthDate" type="month" no-title scrollable color="primary">
    </v-date-picker>
  </v-menu>
</template>

<script>
export default {
  name: 'alphaSelectCalendarDate',
  props: [
    'hideDetails',
    'dense',
    'clearable',
    'clearIcon',
    'prependInnerIcon',
    'multiple',
    'items',
    'itemText',
    'itemValue',
    'label',
    'value',
    'white',
    'title',
    'activation',
    'disabled',
    'done',
    'clear-icon',
    'icon'
  ],
  data () {
    return {
      selectedYearMonthDate: null,
      selectYearMonth: false
    }
  },
  computed: {
    selected: {
      get () {
        return this.value
      },
      set (v) {
        this.$emit('input', v)
        this.$emit('update:selected', v)
      }
    }
  },
  methods: {
    updateYearMonth (selectedYearMonthDate) {
      console.log(selectedYearMonthDate)
      this.$refs.selectYearMonth.save(selectedYearMonthDate)
    },
    isOn (target) {
      return target === ''
    }
    // .v-label--active
    // color: map-get($select-text-color, 'title') !important
    // position: absolute !important
    // transform: translateY(-26px) scale(0.60)
  }
}
</script>
