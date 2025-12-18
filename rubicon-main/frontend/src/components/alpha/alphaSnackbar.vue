<template>

    <v-snackbar class="alpha-snackbar"
      multi-line
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="snackbar.timeout"
      variant="outlined"
      location="top"
    >
        <div class="mb-2 text-high-emphasis">{{ snackbar.title }}</div>
        <p class="">{{ snackbar.message }}</p>
    </v-snackbar>
  </template>
  
  <script setup>
  import { useSnackbarStore } from '@/stores/snackbar';
  
  const snackbar = useSnackbarStore();
  </script>

<style>
.alpha-snackbar > div > div {
  background-color: #212121; /* Set to your preferred color */
}
</style>