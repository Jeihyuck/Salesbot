<template>
  <!-- <v-container fluid class="pa-4 ma-0" :style="{ background: $vuetify.theme.themes.light.background }">
    <v-row>
      <v-col cols="12">
        <alpha-graph-geo :alphaModel="graph1" :show="graphShow"></alpha-graph-geo>
      </v-col>
    </v-row>
    <v-row class="justify-center">
      <a href="https://plotly.com/javascript/continuous-error-bars/" target="_blank">Plotly Band Chart Reference</a>
    </v-row>
    <v-row>
      <v-col cols="4">
        <v-card class="ma-1" outlined style="height: 150px"></v-card>
      </v-col>
      <v-col cols="4">
        <v-card class="ma-1" outlined style="height: 150px"></v-card>
      </v-col>
      <v-col cols="4">
        <v-card class="ma-1"  outlined style="height: 150px"></v-card>
      </v-col>
      </v-row>
  </v-container> -->
</template>
<!-- 
<script>
import alphaGraphGeo from '@/components/alpha/alphaGraphGeo'

export default {
  name: 'ex39',
  components: { alphaGraphGeo },
  data () {
    return {
      graphShow: false,
      graph1: {
        name: 'geoGraph',
        flat: false,
        sizeInfo: {
          margin: 200, // pixel
          stacked: 1
        },
        customLayout: {
          paper_bgcolor: 'rgb(255,255,255)',
          plot_bgcolor: 'rgb(229,229,229)',
          geo: {
            scope: 'usa',
            projection: { type: 'albers usa' },
            showland: true,
            landcolor: '#D3D3D3',
            subunitwidth: 1,
            countrywidth: 1,
            subunitcolor: 'rgb(255,255,255)',
            countrycolor: 'rgb(255,255,255)'
          }
        },
        data: [
          {
            type: 'scattergeo',
            mode: 'markers',
            locations: ['75001', '75002', '75006', '75007'], // Example zip codes
            marker: {
              size: 10,
              color: 'rgb(255, 0, 0)',
              line: {
                color: 'black',
                width: 1
              }
            },
            text: ['Zip code 75001', 'Zip code 75002', 'Zip code 75006', 'Zip code 75007'],
            hoverinfo: 'text'
          }
        ]
      }
    }
  },
  mounted () {
    this.graphShow = true
  }
}
</script> -->
