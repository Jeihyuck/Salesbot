<template>
    <v-text-field
    :clearable="clearable"
    :clear-icon="clearIcon"
    dense
    :disabled="disabled"
    :label="label"
    :hide-details="hideDetails"
    :prepend-inner-icon="prependInnerIcon"
    v-model="inputValue"
    class="alpha-text-input-field-in-table"
    style = "position:relative; bottom:2px; padding-top: 2px;"
    reverse filled
    background-color="accent lighten-3"
    ></v-text-field>
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
    hideDetails: String,
    value: String,
    clearable: {
      type: Boolean,
      default: false
    },
    clearIcon: {
      type: String,
      default: ''
    }
  },
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

<style lang="sass" scoped>
  @import '~@/components/alpha/styles/alphaTextStyles.scss'
  @import '~@/components/alpha/styles/alphaSelect.scss'
  @import '@/alphaColors.scss'

  .alpha-text-input-field-in-table
    color: #eeeeee !important
    &.v-input.v-text-field
      margin: 0
      &.v-input--is-disabled .v-input__slot:before
        border-image: unset !important
      .v-input__control
        // height: 28px !important
        .v-input__slot
          display: flex
          align-items: center
          border-radius: 2px
          padding: 0 8px !important
          min-height: 24px !important
          &:before, &:after
            border: unset !important
          .v-text-field__slot
            padding: 0 !important
            input
              padding: 0 !important
              height: 24px !important

</style>
