<template>
  <v-col class="mx-3 mt-1">
    <v-row class="pb-1">
      <span class="font-weight-black pl-1" v-if="disabled" v-html="currentPageTitle"></span>
    </v-row>
    <v-row class="">
      <router-view />
    </v-row>
  </v-col>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useMenuStore } from '@/stores/menu'
import { useThemeStore } from '@/stores/theme'
// Access the current route
const route = useRoute();

// Access your menu store (if needed)
const menuStore = useMenuStore();

// Reactive variable for the title
const title = ref([]);

// Computed property for 'disabled'
const disabled = computed(() => {
  return route.meta.title !== false;
});

// Computed property for 'currentPageTitle'
const themeStore = useThemeStore()
const currentPageTitle = computed(() => {

  if (route.path === '/') {
    title.value = false;
  } else {
    title.value = menuStore.menuPageTitle[route.path]
  }

  const formatTitle = (item) => {
    return item.replace(/\b\w/g, (char) => char.toUpperCase());
  };

  // Build the HTML title
  if (title.value) {
    const htmlTitle = title.value
      .map(formatTitle)
      .join("<span class='text-primary-darken-1'>&nbsp;&nbsp;>&nbsp;&nbsp;</span>");
    if (themeStore.darkMode) {
      return `<h5 class='text-grey-lighten-2'>${htmlTitle}</h5>`;
    } else {
      return `<h5 class='text-grey-darken-2'>${htmlTitle}</h5>`;
    }
    
  } else {
    return '';
  }
});
</script>
