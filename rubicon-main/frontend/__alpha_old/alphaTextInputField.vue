<template>
  <v-text-field
    flat
    :clearable="clearable"
    :clear-icon="clearIcon"
    dense
    :type="type"
    class="mr-0 pa-0 alpha-text-input-field"
    :disabled="disabled"
    :label="label"
    :hide-details="hideDetails"
    :prepend-inner-icon="prependInnerIcon"
    v-model="inputValue"
  >
    <template v-slot:label>
      <slot name="label"></slot>
    </template>
  </v-text-field>
</template>

<script>
export default {
  name: 'alphaTextInputField',
  props: {
    prependInnerIcon: {
      type: String,
      default: ''
    },
    disabled: [Boolean, Function],
    label: String,
    type: String,
    hideDetails: String,
    value: [Number, String],
    clearable: {
      type: Boolean,
      default: false
    },
    clearIcon: {
      type: String,
      default: ''
    }
  },
  // props: {
  //   prependInnerIcon,
  //   disabled,
  //   label,
  //   type,
  //   hideDetails,
  //   value,
  //   clearable,
  //   clearIcon
  // },
  computed: {
    inputValue: {
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
    click () {
      if (this.onClick != null) {
        this.onClick()
      } else {
        this.$emit('click')
      }
    }
  }
}
</script>

<style lang="sass">
  @import '~@/components/alpha/styles/alphaTextStyles.scss'
  @import '~@/components/alpha/styles/alphaSelect.scss'
  @import '@/alphaColors.scss'

  .alpha-text-input-field
    height: $select-height
    padding: $select-padding
    margin: $select-margin
    border-radius: $select-radius
    &.v-input.v-text-field
      // margin-top: 0
      margin: 0
      &.v-input--is-disabled .v-input__slot:before
        border-image: unset !important
      .v-input__control
        .v-input__slot
          display: flex
          align-items: center
          border-radius: 4px
          background-color: $shade
          height: 32px !important
          &:before
            border: unset !important
          .v-text-field__slot
            padding: 0 4px !important
            label
              left: 0px !important
              &.v-label
                top: 6px !important
                padding: 0 4px !important
              &.v-label--active
                transform: translateY(-10px) scale(0.60) !important
            input
              padding: 0 !important
          .v-input__prepend-inner
            align-self: unset
            margin-left: 8px !important
            margin-right: 2px !important
            padding-right: 0px !important
            &+ .v-text-field__slot
              padding: 0 2px !important
              // label.v-label--active
              //   left: -32px !important
          .v-input__append-inner
            align-self: unset
            margin-right: 8px !important
</style>
