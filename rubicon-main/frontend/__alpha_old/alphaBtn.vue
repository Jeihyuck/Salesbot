<template>
  <v-btn
    :class="style"
    v-bind="attrs"
    v-on="on"
    :large="large"
    :xLarge="xLarge"
    :small="small"
    :xSmall="xSmall"
    :outlined="outlined"
    :disabled="disabled"
    :loading="loading"
    :color="color"
    @click="click"
    v-tooltip="minimize === true ? value : ''"
  >
  {{ getBtnText(value) }}
  </v-btn>
</template>
<script>
export default {
  name: 'alphaBtn',
  computed: {
    style: {
      get () {
        const style = 'ml-1'
        // if (this.light) style += ' light'
        // if (this.mildWarning) style += ' mild-warning'
        return style
      }
    }
  },
  props: {
    value: [Object, String],
    color: [Object, String],
    minimize: Boolean,
    attrs: Object,
    on: Object,
    large: Boolean,
    xLarge: Boolean,
    small: Boolean,
    xSmall: Boolean,
    outlined: Boolean,
    disabled: [Boolean, Function],
    loading: Boolean,
    onClick: Function,
    light: Boolean,
    mildWarning: Boolean
  },
  methods: {
    click () {
      if (this.onClick != null) {
        this.onClick()
      } else {
        this.$emit('click')
      }
    },
    getBtnText (text) {
      if (this.minimize === true) {
        const matches = text.match(/\b(\w)/g) // ['J','S','O','N']
        const acronym = matches.join('')
        return acronym
      } else {
        return text
      }
    }
  }
}
</script>
