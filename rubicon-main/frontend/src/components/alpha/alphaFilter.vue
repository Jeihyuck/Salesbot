<template>
  <v-card class="w-100" >
    <v-row :class="alphaFilterPadding">
    <!-- <v-row class="pa-3"> -->
    <v-col cols="11">
      <alphaFilter-items v-if="isLevel3" :alphaModel="alphaModel" :level="3"></alphaFilter-items>
      <alphaFilter-items v-if="isLevel2" :alphaModel="alphaModel" :level="2"></alphaFilter-items>
      <alphaFilter-items :alphaModel="alphaModel" :level="undefined"></alphaFilter-items>
    </v-col>
    <v-col cols="1" align-self="end" v-if="alphaModel.filter.instanceSearch !== true" class="text-right pl-0 pr-1 pt-1 pb-2">
      <v-btn
        class="my-auto mr-2 mb-2 px-0"
        color="primary"
        height="32"
        @click="search"
        >Search</v-btn>
      <slot name="filterButtons"></slot>
    </v-col>
    </v-row>
  </v-card>
  <!-- <v-card class="w-100" >
    <v-row class="pa-3">
    <v-col cols="11">
      <alphaFilter-items v-if="isLevel3" :alphaModel="alphaModel" :level="3"></alphaFilter-items>
      <alphaFilter-items v-if="isLevel2" :alphaModel="alphaModel" :level="2"></alphaFilter-items>
      <alphaFilter-items :alphaModel="alphaModel" :level="undefined"></alphaFilter-items>
    </v-col>
    <v-col cols="1" align-self="end" v-if="alphaModel.filter.instanceSearch !== true" class="text-right pl-0 pr-1 pt-1 pb-2">
      <v-btn
        class="my-auto mr-2 mb-1 px-0"
        color="primary"
        height="32"
        @click="filteringTable"
        >Search</v-btn>
      <slot name="filterButtons"></slot>
    </v-col>
    </v-row>
  </v-card> -->
</template>

<script>
import alphaFilterItems from '@/components/alpha/alphaFilterItems'

export default {
  name: 'alphaFilter',
  components: { alphaFilterItems },
  props: ['alphaModel'],
  data () {
    return {
      isLevel2: false,
      isLevel3: false
    }
  },
  asyncComputed: {
    alphaFilterPadding () {
      console.log('alphaModel.filter.hideBoarder', this.alphaModel.filter.hideBoarder)
      if (this.alphaModel.filter.hideBoarder === true) {
        return 'pb-3 pt-2 pl-0 pr-0'
      } else {
        return 'pa-3'
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
    onFilterSet (key, value) {
      this.$emit('update:filter', {
        key: k,
        value: v
      })
    },
    search () {
      this.$emit('search')
    }
  }
}

</script>
