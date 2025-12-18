<template>
  <v-container fluid class="pa-4 ma-0" :style="{ background: $vuetify.theme.themes.light.background }">
    <alphaDataTable-view :alphaModel="ex25">
      <template v-slot:calory_custom="{ item }">
        <div> {{ getCommaFormat(item.calory) }} cal</div>
      </template>
      <template v-slot:likeing_custom="{ item }">
        <div> {{ item.likeing? 'Y':'-' }}</div>
      </template>
    </alphaDataTable-view>
  </v-container>
</template>

<script>
import alphaDataTableView from '@/components/alpha/alphaDataTableView'
import { alphaExample } from '@/_services'
import { template, numberWithCommas, floatToFixed } from '@/_helpers'

export default {
  name: 'ex12',
  components: { alphaDataTableView },
  data () {
    return {
      ex25: {
        name: 'EX25',
        function: alphaExample.ex12.ex12Function,
        crud: [true, true, true, true],
        headerId: 'ca84889e-de87-4757-b2b2-a9fd3c5635db',
        pagination: true,
        fullLoad: true,
        sortBy: ['category_name', 'name'],
        sortDesc: [true, true],
        customFields: ['calory', 'likeing'],
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
        dialogWidth: '400px',
        dialog: {
          name: {
            name: 'Fruit Name',
            type: 'input',
            disabled: () => {
              if (this.ex25.status.editType === 'EDIT') {
                return true
              } else {
                return false
              }
            },
            required: true,
            selected: ''
          },
          notes: template.fields.OPTIONAL_INPUT('Notes'),
          category__name: {
            name: 'Category',
            type: 'dropdown',
            multiple: false,
            disabled: () => {
              return false
            },
            required: true,
            selector: [{ text: 'Fruits', value: 'Fruits' }, { text: 'Protain Foods', value: 'Protain Foods' }],
            selected: ''
          },
          calory: template.fields.OPTIONAL_NUMBER('Calory'),
          likeing: {
            name: 'Likeing',
            type: 'dropdown',
            multiple: false,
            disabled: () => {
              return false
            },
            required: true,
            selector: [{ text: 'Y', value: true }, { text: 'N', value: false }],
            selected: ''
          }
        }
      }
    }
  },
  methods: {
    getCommaFormat (value) {
      return numberWithCommas(floatToFixed(value))
    }
  }
}
</script>
