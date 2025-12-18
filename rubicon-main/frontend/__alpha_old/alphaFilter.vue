<template>
  <div :style="cardStyle">
    <v-row :class="outerRowClass">
      <v-col cols="12" class="px-0 mx-0 my-0 pt-0 pb-0">
        <v-card :class="cardClass">
          <v-row class="pb-0">
          <v-col cols="11" align-self="center" class="px-0 pb-0 ma-0">
            <alphaFilter-items v-if="isLevel3" :alphaModel="alphaModel" class="pt-4 pb-1 mt-n2" :level="3"></alphaFilter-items>
            <alphaFilter-items v-if="isLevel2" :alphaModel="alphaModel" class="pt-5 pb-1 mt-n3" :level="2"></alphaFilter-items>
            <alphaFilter-items :alphaModel="alphaModel" class="pt-4 pb-2 mt-n2" :level="undefined"></alphaFilter-items>
          </v-col>
          <v-col cols="1" align-self="end" v-if="alphaModel.filter.instanceSearch !== true" class="text-right pl-0 pr-1 pt-1 pb-2">
            <v-btn
              class="my-auto mr-2 px-0"
              color="primary"
              height="32"
              @click="filteringTable"
              >Search</v-btn>
            <slot name="filterButtons"></slot>
          </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>


<script>
import { mdiClose, mdiMagnify, mdiCalendarToday, mdiCalendarMonth, mdiCalendarWeek, mdiClockTimeFourOutline } from '@mdi/js'
import alphaFilterItems from '@/components/alpha/alphaFilterItems'

export default {
name: 'alphaFilter',
components: { alphaFilterItems },
props: ['alphaModel'],
data () {
  return {
    icons: {
      mdiMagnify: mdiMagnify,
      mdiCalendarToday: mdiCalendarToday,
      mdiCalendarMonth: mdiCalendarMonth,
      mdiCalendarWeek: mdiCalendarWeek,
      mdiClockTimeFourOutline: mdiClockTimeFourOutline,
      mdiClose: mdiClose
    },
    isLevel2: false,
    isLevel3: false
  }
},
asyncComputed: {
  outerRowClass () {
    if (this.alphaModel.filter.hideBoarder === true) {
      return 'justify-space-between pa-0 my-0 ml-n7 mr-n4'
    } else {
      return 'justify-space-between mx-0 pt-0 pb-0'
    }
  },
  cardClass () {
    if (this.alphaModel.filter.hideBoarder === true) {
      return 'ml-2 mr-1 px-0 mx-0 py-0 pl-2 elevation-0'
    } else {
      return 'mt-0 mb-3 px-0 mx-0 pb-1 pt-1 elevation-1'
    }
  },
  cardStyle () {
    if (this.alphaModel.filter.hideBoarder === true) {
      return '{ background-color:transparent; }'
    } else {
      return '{ background: $vuetify.theme.themes.light.background }'
    }
  }
},
watch: {
  'alphaModel.filter': {
    deep: true,
    handler () {
      if (this.alphaModel.filter.instanceSearch === true) {
        console.log('instanceSearch')
        this.filteringTable()
      }
    }
  }
},
mounted () {
  this.checkFilterLevel()
},
methods: {
  checkFilterLevel () {
    Object.entries(this.alphaModel.filter).forEach(([key, value]) => {
      if (this.alphaModel.filter[key].level) {
        if (value.level === 2) {
          this.isLevel2 = true
        }
        if (value.level === 3) {
          this.isLevel3 = true
        }
      }
    })
  },
  getIcon (icon) {
    return this.icons[icon]
  },
  onFilterSet (k, v) {
    this.$emit('update:filter', {
      key: k,
      value: v
    })
  },
  filteringTable () {
    this.$emit('click:filter', this.alphaModel)
  }
}
}
</script>
