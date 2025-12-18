<template>
  <!-- <v-container fluid class="pa-4 ma-0" :style="{ background: $vuetify.theme.themes.light.background }">
    <v-row>
      <v-col cols="4">
        <alpha-graph-basic :alphaModel="graph1" :show="graphShow"></alpha-graph-basic>
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
import alphaGraphBasic from '@/components/alpha/alphaGraphBasic'

export default {
  name: 'ex12',
  components: { alphaGraphBasic },
  data () {
    return {
      graphShow: false,
      graph1: {
        name: 'graph1',
        flat: false,
        sizeInfo: {
          margin: 400, // pixel
          stacked: 1
        },
        customLayout: {
          paper_bgcolor: 'rgb(255,255,255)',
          plot_bgcolor: 'rgb(229,229,229)',
          xaxis: {
            gridcolor: 'rgb(255,255,255)',
            range: [1, 10],
            showgrid: true,
            showline: false,
            showticklabels: true,
            tickcolor: 'rgb(127,127,127)',
            ticks: 'outside',
            zeroline: false
          },
          yaxis: {
            gridcolor: 'rgb(255,255,255)',
            showgrid: true,
            showline: false,
            showticklabels: true,
            tickcolor: 'rgb(127,127,127)',
            ticks: 'outside',
            zeroline: false
          }
        },
        data: [{
          x: [1, 2, 3, 4, 6, 6, 7, 8, 9, 10, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
          y: [2, 5, 4, 5, 6, 7, 8, 9, 10, 11, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
          fill: 'tozerox',
          fillcolor: 'rgba(0,100,80,0.2)',
          line: { color: 'transparent' },
          name: 'Fair',
          showlegend: false,
          type: 'scatter'
        }]
      }
    }
  },
  mounted () {
    this.graphShow = true
  }
}
</script> -->
