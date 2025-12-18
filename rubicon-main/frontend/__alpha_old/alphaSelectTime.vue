<template>
  <v-menu ref="selectTime" v-model="selectTime"
    :close-on-content-click="false"
    :nudge-right="40"
    :return-value.sync="selected"
    transition="scale-transition"
    offset-y max-width="290px" min-width="290px"
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
    <v-time-picker
      @change="updateTime(selectedTime)"
      v-model="selectedTime"
      full-width
      @click:minute="$refs.selectTime.save(selectedTime)"
    ></v-time-picker>
  </v-menu>
</template>

<script>
export default {
  name: 'alphaSelectTime',
  props: [
    'hideDetails',
    'dense',
    'clearable',
    'clearIcon',
    'prependInnerIcon',
    // 'multiple',
    // 'items',
    // 'itemText',
    // 'itemValue',
    'label',
    'value',
    // 'white',
    // 'title',
    // 'activation',
    'disabled',
    'done',
    'clear-icon',
    'icon'
  ],
  data () {
    return {
      selectedTime: null,
      selectTime: false
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
  // watch: {
  //   selected () {
  //     console.log(this.selected)
  //   }
  // },
  methods: {
    updateTime (selectedTime) {
      console.log(selectedTime)
      this.$refs.selectTime.save(selectedTime)
    },
    isOn (target) {
      return target === ''
    }
  }
}
</script>
