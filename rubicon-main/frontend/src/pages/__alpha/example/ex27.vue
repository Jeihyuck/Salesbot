<template>
  <v-container fluid class="pa-4 ma-0" :style="{ background: $vuetify.theme.themes.light.background }">
    <alphaDataTable-view :alphaModel="ex27">
    </alphaDataTable-view>
  </v-container>
</template>

<script>
import alphaDataTableView from '@/components/alpha/alphaDataTableView'
import { alphaExample } from '@/_services'

export default {
  name: 'ex12',
  components: { alphaDataTableView },
  data () {
    return {
      ex27: {
        name: 'EX27',
        function: alphaExample.ex12.ex12Function,
        crud: [false, true, false, false],
        headerId: 'ca84889e-de87-4757-b2b2-a9fd3c5635db',
        pagination: true,
        fullLoad: true,
        filter: {
          hideBoarder: false,
          category: {
            name: 'Category',
            type: 'dropdown',
            clearable: true,
            multiple: false,
            selector: ['Fruits', 'Protain Foods', 'Vegetables', 'Grains'],
            selected: '',
            col: 3
          },
          search: {
            name: '검색',
            type: 'search',
            selected: '',
            col: 3
          },
          searchScope: {
            name: '',
            type: 'radio',
            selector: [{ text: '전체', value: 'all' }, { text: 'Likeing', value: 'likeing' }],
            selected: 'all',
            col: 3
          }
        },
        excel: {
          download: {
            fuctionUrl: 'api/example/ex12/',
            action: 'readIngredients',
            template: 'example',
            filename: 'example.xlsx'
          },
          upload: {
            fuctionUrl: 'api/example/ex12/',
            action: 'updateIngredients',
            template: [
              {
                field: 'name',
                label: 'Name',
                type: 'string',
                width: '40px'
              },
              {
                field: 'category',
                label: 'Category',
                type: 'string',
                width: '40px'
              }
            ]
          }
        }
      }
    }
  }
}
// https://github.com/cscan/vue-excel-editor
</script>
