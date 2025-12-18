<template>
  <v-layout>
    <v-app-bar v-if="$route.meta.showAppBar && !envStore.isMobile" density="compact" @click.stop="toggleDrawer">
      <template v-if="hideDrawer === false" v-slot:prepend>
        <v-app-bar-nav-icon></v-app-bar-nav-icon>
      </template>
      <!-- <img class="ml-4 mb-0 pb-0" src="@/assets/samsung_logo.png" style="width: 150px; height: 50px"> -->
      <v-app-bar-title v-if="hideDrawer === false" class="font-weight-black">Rubicon Admins</v-app-bar-title>
      <v-app-bar-title v-else class="font-weight-black">Rubicon Chat Test</v-app-bar-title>
    </v-app-bar>
    <v-navigation-drawer v-if="$route.path !== '/' && !envStore.value && hideDrawer === false" floating v-model="drawer">
      <alpha-menu-items :items="menuStore.menuTree" />
    </v-navigation-drawer>
    <v-main class="d-flex justify-center">
      <RouterView></RouterView>
    </v-main>
    <alpha-snackbar />
  </v-layout>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router' // For accessing the route object
import alphaSnackbar from '@/components/alpha/alphaSnackbar'
import { useAuthStore } from '@/stores/auth'
import { useMenuStore } from '@/stores/menu'
import { useEnvStore } from '@/stores/env'
import alphaMenuItems from '@/components/alpha/alphaMenuItems.vue';


const drawer = ref(true)
const hideDrawer = ref(false)
const menuStore = useMenuStore()
const envStore = useEnvStore()
const authStore = useAuthStore()

// const isMobile = ref(false);

onMounted(() => {
  envStore.isMobile = /Mobi|Android/i.test(navigator.userAgent);
  // console.log('mobile', envStore.isMobile)
});

function toggleDrawer() {
  drawer.value = !drawer.value;
}

const route = useRoute();

watch(
  () => authStore.isAuthenticated,
  (newMeta) => {
    // console.log(JSON.parse(JSON.stringify(authStore.group)))
    const group = JSON.parse(JSON.stringify(authStore.group))

    if (group.includes('ADMIN') || group.includes('DEV')) {
      hideDrawer.value = false
    } else {
      hideDrawer.value = true
    }
  },
  { deep: true } // Watch for nested changes in the meta object
);


watch(
  () => route.meta,
  (newMeta) => {
    drawer.value = newMeta.showNavDrawer; // Update the drawer state when meta changes
  },
  { deep: true } // Watch for nested changes in the meta object
);

</script>

<style>

html { overflow-y: auto }

.v-btn {
  text-transform:none !important;
}

.v-btn--size-x-small {
  min-width: 24px !important;
}

.sub-menu-item {
  color: #cedbec !important;
}

.code-blck-header {
  font-size: 0.8em;
  font-family: Menlo, Monaco, Consolas, "Andale Mono", "Ubuntu Mono", "Courier New", monospace;
  background-color: #343541;
  color: white;
  padding: 4px 0px 2px 10px;
  border-top-left-radius: 4px;   /* adjust the value as needed */
  border-top-right-radius: 4px;
  display: flex;
  width: 100%;
  justify-content: space-between;
}

.splitpanes__pane {
  padding: 2px;
}

.splitpanes__splitter {
  background-color: rgba(100, 100, 100) !important;
  margin: 2px;
  padding: 2px;
}

/* width */
::-webkit-scrollbar {
  width: 5px;
}

/* Track */
::-webkit-scrollbar-track {
  background: hwb(0 17% 83%);
}

/* Handle */
::-webkit-scrollbar-thumb {
  background: hsl(240, 1%, 37%);
}

/* Handle on hover */
/* ::-webkit-scrollbar-thumb:hover {
  background: #555;
} */
code {
  white-space : pre-wrap !important;
  word-break: break-word;
}

</style>