<template>
  <v-select
    :hide-details="hideDetails"
    :clear-icon="clearIcon"
    :dense="dense"
    :clearable="clearable"
    :multiple="multiple"
    :items="items"
    :item-value="item => itemValue(item)"
    :prepend-inner-icon="prependInnerIcon"
    :disabled="disabled"
    v-model="selected"
    class="alpha-select"
    :class="{
      'alpha-input__default': !isOn(white),
      'alpha-input__white': isOn(white),
      'alpha-input-style__default': !isOn(title) & !isOn(activation) & !isOn(done) & !isOn(disabled),
      'alpha-input-style__title': isOn(title),
      'alpha-input-style__activation': isOn(activation),
      'alpha-input-style__done': isOn(done)
    }"
  >
    <template v-slot:selection="{ item, index }">
      <span v-if="maxDisplay === undefined">{{ itemText(item, index) }} &nbsp;</span>
      <span v-if="maxDisplay !== undefined && index < maxDisplay">{{ itemText(item, index) }} &nbsp;</span>
      <span
        v-if="maxDisplay !== undefined && index === maxDisplay"
        class="grey--text caption"
      >(+{{ selected.length - maxDisplay }})</span>
      <!-- </div> -->
    </template>
    <!-- :clear-icon="clearIcon" -->
    <template v-slot:label>
      <slot name="label">
        <span>{{customLabel}}</span>
      </slot>
    </template>
  </v-select>
</template>

<script>
// :item-text="item => itemText(item)"
export default {
  name: 'alphaSelect',
  props: [
    'hideDetails',
    'dense',
    'clearable',
    'clearIcon',
    'prependInnerIcon',
    'multiple',
    'items',
    'label',
    'labelTranform',
    'value',
    'white',
    'title',
    'activation',
    'disabled',
    'done',
    'maxDisplay'
  ],
  computed: {
    selected: {
      get () {
        return this.value
      },
      set (v) {
        this.$emit('input', v)
        this.$emit('update:selected', v)
      }
    },
    customLabel () {
      if (this.labelTranform === undefined || this.labelTranform === true) {
        // console.log('Normal Transfrom Label')
        return this.label
      } else {
        if (this.selected === '' || this.selected === []) {
          // console.log('No Item Has selected')
          return this.label
        } else {
          // console.log('Item Has selected')
          return ''
        }
      }
    }
  },
  methods: {
    itemValue (item) {
      if (item.value === undefined) {
        return item
      } else {
        return item.value
      }
    },
    itemText (item, index) {
      // console.log(item, index, this.selected)
      if (item.text === undefined) {
        if (index === this.selected.length - 1) {
          return item
        } else {
          if (this.multiple === true) {
            return item + ','
          } else {
            return item
          }
        }
      } else {
        if (index === this.selected.length - 1) {
          return item.text
        } else {
          if (this.multiple === true) {
            return item.text + ','
          } else {
            return item.text
          }
        }
      }
    },
    isOn (target) {
      return target === ''
    }
  }
}
</script>

<style lang="sass">
  @import '~@/components/alpha/styles/alphaSelect.scss'

  .alpha-select
    height: $select-height
    padding: $select-padding
    margin: $select-margin
    border-radius: $select-radius
    vertical-align: middle

    *
      letter-spacing: 0

    div
      margin: auto

    label
      left: -2px !important
      &.v-label
        top: 0
      &.v-label--active
        transform: translateY(-10px) scale(0.60)

    .v-input__prepend-inner
      align-self: unset
      margin-left: 0px !important
      &+ .v-select__slot
        padding: 0 0px !important
        label.v-label--active
          left: -24px !important
    // .v-input__append-inner
    //   .v-input__icon--clear
    //     padding-top: 30px !important

    ::before, ::after
      border: none !important

    $input-types: 'default'

    @each $name1 in $input-types
      &.alpha-input__#{$name1}
        background-color: map-get($select-bg-color, $name1)
        // outline-color: $gray !important
        // outline-style: solid
        // outline-width: 1px !important

        .v-select__selection, .v-input__append-inner, .v-input__append-inner *
          color: map-get($select-text-color, $name1, 'title') !important
          padding-top: 2px !important
          padding-left: 0 !important
          margin: 0 !important

        $input-style-types: 'default', 'title', 'activation', 'disabled', 'done'
        @each $name2 in $input-style-types
          &.alpha-input-style__#{$name2}
            *
              color: map-get($select-text-color, $name1, $name2)
</style>
