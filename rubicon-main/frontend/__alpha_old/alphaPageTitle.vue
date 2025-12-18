<template>
  <v-toolbar :style="{ background: $vuetify.theme.themes.light.pageTitle }" class="pl-5 pt-1 alphaPageTitle" short elevation=0>
    <v-toolbar-title class="text-h6 font-weight-bold pb-1">
    {{title}}
    </v-toolbar-title>
  </v-toolbar>
</template>

<script>
export default {
  name: 'alphaPageTitle',
  props: {
    title: {
      type: String,
      default: 'Page title has not defined'
    }
  }
  // computed: {
  //   titleColor () {
  //     return this.$Color(this.$vuetify.theme.themes.light.primary).desaturate(0.4).lighten(0.55).string()
  //   }
  // }
}
</script>

<style>
.alphaPageTitle {
  position: sticky !important;
  top: var(--headerHeight);
  z-index: 2;
}
</style>
