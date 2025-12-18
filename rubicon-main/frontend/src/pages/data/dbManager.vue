<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">
    <v-row class="pt-0 px-0" density="dense">
      <v-col cols="12" class="px-0">
        <v-card>
          <v-tabs v-model="tab" bg-color="primary">
            <v-tab value="one">Add CPT Keywords</v-tab>
            <v-tab value="two">Update/Delete CPT Keywords</v-tab>
          </v-tabs>
          <v-card-text>
            <v-tabs-window v-model="tab">
              <v-tabs-window-item value="one">
                <CPTKeywordAddPanel />
              </v-tabs-window-item>
              <v-tabs-window-item value="two">
                <CPTKeywordManagePanel />
              </v-tabs-window-item>
            </v-tabs-window>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-col>
</template>

<script setup>
import { ref } from 'vue'
const tab = ref('one')
</script>
