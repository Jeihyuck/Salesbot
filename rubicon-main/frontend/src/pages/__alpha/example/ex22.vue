<template>
  <v-container fluid class="pa-4 ma-0" :style="{ background: $vuetify.theme.themes.light.background }">
    <alphaDataTable :alphaModel="ex12"></alphaDataTable>
    <alphaDataTable-view :alphaModel="ex12"></alphaDataTable-view>
  </v-container>
</template>

<script>
import alphaDataTable from '@/components/alpha/alphaDataTable'
import alphaDataTableView from '@/components/alpha/alphaDataTableView'
import { alphaExample } from '@/_services'

export default {
  name: 'ex12',
  components: { alphaDataTable, alphaDataTableView },
  data () {
    return {
      ex12: {
        name: 'ex12',
        function: alphaExample.ex12.ex12Function,
        crud: [false, true, false, false],
        headerId: 'ca84889e-de87-4757-b2b2-a9fd3c5635db',
        pagination: false,
        dataMap: {
          likeing: (row) => {
            row.likeing = row.likeing === true ? 'Y' : '-'
          }
        }
      }
    }
  }
}
</script>
