<!-- <template>
<v-container fill-height d-flex fluid>
  <div class="center">
  <p>This text is centered.</p>
  </div>
  <v-row justify="center"  align="center">
    <v-col>
      <div class="alpha-text-field text-md-center text-lg-center" style="vertical-align: middle !important;"> {{label}} </div>
      <v-text-field flat hide-details read-only v-model="label"></v-text-field>
    </v-col>
  </v-row>
</v-container>
</template> -->
<template>
<div class="container">
  <div class="center">
    <p class="ma-0 pa-0">{{label}}</p>
  </div>
</div>
</template>

<script>
export default {
  name: 'alphaTextField',
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

<style lang="css" scoped>
.container {
  height: 100%;
  position: relative;
}

.center {
  margin: 0;
  position: absolute;
  top: 50%;
  left: 50%;
  -ms-transform: translate(-50%, -50%);
  transform: translate(-50%, -50%);
}
</style>
