<template>
  <v-autocomplete
    class="alpha-autocomplete"
    :hide-details="hideDetails"
    dense
    :disabled="disabled"
    :clearable="clearable"
    :multiple="multiple"
    :items="items"
    :item-text="itemText"
    :item-value="itemValue"
    :label="label"
    v-model="selected"
  >
    <template v-slot:label>
      <slot name="label"></slot>
    </template>
  </v-autocomplete>
</template>

<script>
export default {
  name: 'alphaAutocomplete',
  props: {
    hideDetails: [Boolean, String],
    multiple: {
      type: Boolean,
      default: false
    },
    label: String,
    clearable: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    },
    items: [Array, Object],
    itemText: Function,
    itemValue: Function,
    value: [String, Object, Array]
  },
  computed: {
    selected: {
      get () {
        return this.value
      },
      set (v) {
        this.$emit('input', v)
      }
    }
  }
}
</script>

<style lang="sass">
  @import '@/alphaColors.scss'
  @import '~@/components/alpha/styles/alphaSelect.scss'

  .alpha-autocomplete
    label
      // font: map-get($select-font, 'select-input') !important
      &.v-label
        top: 0 !important
      &.v-label--active
        transform: translateY(-26px) scale(0.60)
    input
      align-self: unset
      padding: 0 !important
    &.v-input.v-text-field
      margin-top: 0
      .v-input__control
        .v-input__slot
          padding: 0 16px
          border-radius: 8px
          background-color: $shade
          height: 44px
          .v-select__slot
            display: flex
            align-items: center
          &:before
            border: unset !important
</style>
