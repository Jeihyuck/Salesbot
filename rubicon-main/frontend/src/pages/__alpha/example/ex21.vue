<template>
  <v-container fluid class="pa-4 ma-0" :style="{ background: $vuetify.theme.themes.light.background }">
    <alphaFilter :alphaModel="ex21a"></alphaFilter>
    <div class="py-4"></div>
    <alphaFilter :alphaModel="ex21b"></alphaFilter>
  </v-container>
</template>

<script>
import alphaFilter from '@/components/alpha/alphaFilter'
import { alphaExample } from '@/_services'

export default {
  name: 'ex12',
  components: { alphaFilter },
  data () {
    return {
      ex21a: {
        filter: {
          hideBoarder: false,
          category: {
            name: 'Category',
            type: 'dropdown',
            clearable: true,
            multiple: false,
            selector: ['Fruits', 'Protain Foods', 'Vegetables', 'Grains'],
            selected: 'Fruits',
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
            selector: [{ text: '전체', value: 'all' }, { text: '일부', value: 'part' }],
            selected: 'part',
            col: 3,
            level: 3
          },
          categorySecond: {
            name: 'Category',
            type: 'dropdown',
            clearable: true,
            multiple: true,
            maxDisplay: 2,
            selector: [{ text: 'Fruits', value: 0 }, { text: 'Vegetables', value: 1 }, { text: 'Grains', value: 2 }, { text: 'Protain Foods', value: 3 }],
            selected: [0, 1, 2],
            level: 2,
            col: 4
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
      },
      ex21b: {
        filter: {
          hideBoarder: true,
          category: {
            name: 'Category',
            type: 'dropdown',
            clearable: true,
            multiple: false,
            selector: [{ text: 'Fruits', value: 0 }, { text: 'Vegetables', value: 1 }],
            selected: 0,
            col: 3
          },
          search: {
            name: '검색',
            type: 'input',
            selected: '',
            col: 8
          }
        }
      }
    }
  }
}
</script>
