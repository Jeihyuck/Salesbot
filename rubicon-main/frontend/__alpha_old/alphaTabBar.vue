<template>
  <v-container fluid class="px-0 mt-0 pt-0">
    <v-tabs
      :background-color="String(this.$vuetify.theme.themes.light.pageTitle)"
      v-model="tab"
      class="elevation-1 alphaTabBar"
      height="35px"
      center-active show-arrows
    >
      <v-tab v-for="item in items" :key="item.tab">
        {{ item.tab }}
      </v-tab>
    </v-tabs>
    <v-tabs-items v-model="tab">
      <v-tab-item v-for="item in items" :key="item.tab">
        <component v-if="item.components" :is="item.components"/>
        <slot v-else name="tab" :tabName="item.tab" :item="item" :tab="tab"></slot>
      </v-tab-item>
    </v-tabs-items>
  </v-container>
</template>

<script>
export default {
  name: 'alphaTabBar',
  props: {
    items: Array,
    isSecondary: {
      type: Boolean,
      default: false
    },
    isTertiary: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    tab: {
      get () {
        return this.tab_
      },
      set (v) {
        this.$emit('tabChanged', v)
        this.tab_ = v
      }
    }
  },
  data () {
    return {
      tab_: ''
    }
  },
  methods: {
    forceTab (t) {
      this.tab = t
    }
  }
}
</script>

<style scoped>
.alphaTabBar {
  position: sticky !important;
  position: -webkit-sticky !important;
  top: var(--titleHeight);
  z-index: 2;
}
</style>
