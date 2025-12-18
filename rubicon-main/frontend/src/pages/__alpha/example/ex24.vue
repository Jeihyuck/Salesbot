<template>
  <v-container fluid class="pa-4 ma-0" :style="{ background: $vuetify.theme.themes.light.background }">
    <alphaDataTable-view :alphaModel="ex24a"></alphaDataTable-view>
    <alphaDataTable-view :alphaModel="ex24b" class="mt-4"></alphaDataTable-view>
    <alphaDataTable-view :alphaModel="ex24c" class="mt-4"></alphaDataTable-view>
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
      ex24a: {
        name: 'ex24a',
        function: alphaExample.ex12.ex12Function,
        crud: [false, true, false, false],
        headerId: 'ca84889e-de87-4757-b2b2-a9fd3c5635db',
        pagination: false,
        filter: {
          hideBoarder: false,
          company: {
            name: 'Category',
            type: 'dropdown',
            clearable: true,
            multiple: false,
            selector: ['Fruits', 'Protain Foods', 'Vegetables', 'Grains'],
            selected: '',
            level: 3,
            col: 3
          },
          test: {
            name: '설명',
            type: 'text',
            level: 3,
            col: 3
          },
          searchScope: {
            name: '',
            type: 'radio',
            selector: [{ text: '전체', value: 'all' }, { text: '경쟁', value: 'competitorNotSet' }],
            selected: 'competitorNotSet',
            col: 3,
            level: 3
          },
          companySecond: {
            name: 'Category',
            type: 'dropdown',
            clearable: true,
            multiple: true,
            maxDisplay: 2,
            selector: ['Fruits', 'Protain Foods', 'Vegetables', 'Grains'],
            selected: '',
            level: 2,
            col: 3
          },
          creationDate: {
            name: 'Creation Date',
            type: 'yearMonthDate',
            selected: '',
            disabled: false,
            level: 2,
            col: 3
          },
          creationTime: {
            name: 'Creation Time',
            type: 'time',
            selected: '',
            disabled: false,
            level: 2,
            col: 3
          },
          search: {
            name: '검색',
            type: 'search',
            selected: '',
            col: 4
          },
          creationDatetime: {
            name: ['Creation Date', 'Creation Time'],
            type: 'yearMonthDateTime',
            selected: ['', ''],
            disabled: false,
            col: 3
          }
        }
      },
      ex24b: {
        name: 'ex24a',
        function: alphaExample.ex12.ex12Function,
        crud: [false, true, false, false],
        headerId: 'ca84889e-de87-4757-b2b2-a9fd3c5635db',
        pagination: false,
        filter: {
          hideBoarder: false,
          companySecond: {
            name: 'Category',
            type: 'dropdown',
            clearable: true,
            multiple: true,
            maxDisplay: 2,
            selector: ['Fruits', 'Protain Foods', 'Vegetables', 'Grains'],
            selected: '',
            level: 2,
            col: 3
          },
          creationDate: {
            name: 'Creation Date',
            type: 'yearMonthDate',
            selected: '',
            disabled: false,
            level: 2,
            col: 3
          },
          creationTime: {
            name: 'Creation Time',
            type: 'time',
            selected: '',
            disabled: false,
            level: 2,
            col: 3
          },
          search: {
            name: '검색',
            type: 'search',
            selected: '',
            col: 4
          },
          creationDatetime: {
            name: ['Creation Date', 'Creation Time'],
            type: 'yearMonthDateTime',
            selected: ['', ''],
            disabled: false,
            col: 3
          }
        }
      },
      ex24c: {
        name: 'ex14b',
        function: alphaExample.ex12.ex12Function,
        crud: [false, true, false, false],
        headerId: 'ca84889e-de87-4757-b2b2-a9fd3c5635db',
        pagination: false,
        filter: {
          hideBoarder: true,
          company: {
            name: 'Category',
            type: 'dropdown',
            clearable: true,
            multiple: false,
            selector: ['Fruits', 'Protain Foods', 'Vegetables', 'Grains'],
            selected: '',
            level: 3,
            col: 3
          },
          test: {
            name: '설명',
            type: 'text',
            level: 3,
            col: 3
          },
          searchScope: {
            name: '',
            type: 'radio',
            selector: [{ text: '전체', value: 'all' }, { text: '경쟁', value: 'competitorNotSet' }],
            selected: 'competitorNotSet',
            col: 3,
            level: 3
          },
          companySecond: {
            name: 'Category',
            type: 'dropdown',
            clearable: true,
            multiple: true,
            maxDisplay: 2,
            selector: ['Fruits', 'Protain Foods', 'Vegetables', 'Grains'],
            selected: '',
            level: 2,
            col: 3
          },
          creationDate: {
            name: 'creationDate',
            type: 'yearMonthDate',
            selected: '',
            disabled: false,
            level: 2,
            col: 3
          },
          creationTime: {
            name: 'creationTime',
            type: 'time',
            selected: '',
            disabled: false,
            level: 2,
            col: 3
          },
          search: {
            name: '검색',
            type: 'input',
            selected: '',
            col: 4
          },
          creationDatetime: {
            name: ['creationDate', 'creationTime'],
            type: 'yearMonthDateTime',
            selected: ['', ''],
            disabled: false,
            col: 3
          }
        }
      }
    }
  }
}
</script>
