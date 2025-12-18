<template>
  <v-textarea
    :clearable="clearable"
    class="mr-0 pa-0 custom-textarea font-weight-bold"
    :disabled="disabled"
    :label="label"
    :hide-details="hideDetails"
    v-model="inputValue"
    background-color="#1E1E1E" filled auto-grow
    :outlined="outlined"
    :counter="counter"
  >
    <template v-slot:label>
      <slot name="label"></slot>
    </template>
  </v-textarea>
</template>

<script>
export default {
  name: 'alphaTextArea',
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
    outlined: {
      type: Boolean,
      default: true
    },
    counter: {
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
