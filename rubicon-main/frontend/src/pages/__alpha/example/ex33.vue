<template>
  <!-- <v-container fluid class="pa-4 ma-0" :style="{ background: $vuetify.theme.themes.light.background }">
    <v-row>
      <v-col cols="4" class="pr-2">
        <alpha-graph-basic :alphaModel="graph1" :show="graphShow"></alpha-graph-basic>
      </v-col>
      <v-col cols="4" class="px-1">
        <alpha-graph-basic :alphaModel="graph2" :show="graphShow"></alpha-graph-basic>
      </v-col>
    </v-row>
    <v-row class="justify-center">
      <a href="https://plotly.com/javascript/line-and-scatter/" target="_blank">Plotly Scatter Chart Reference</a>
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
        flat: false,
        sizeInfo: {
          margin: 400, // pixel
          stacked: 1
        },
        customLayout: {
          showlegend: false,
          yaxis: {
            autorange: false,
            range: [150, 160]
          },
          xaxis: {
            autorange: false,
            range: [1, 29]
          }
        },
        data: [{
          x: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
          y: [155.57, 155.58, 155.62, 155.68, 155.74, 155.7, 155.67, 155.69, 155.71, 155.75, 155.85, 155.86, 155.83, 155.79, 155.78, 155.81, 155.85, 155.93, 155.91, 155.87, 155.87, 155.86, 155.89, 155.92, 155.99, 155.94, 155.92, 155.93, 155.95],
          name: '경쟁 주유소',
          mode: 'lines'
        }]
      },
      graph2: {
        sizeInfo: {
          margin: 400, // pixel
          stacked: 1,
          innerPadding: 50
        },
        title: '자사/경쟁사 주유소 점두가 추이',
        customLayout: {
          showlegend: true,
          margin: { l: 20, r: 20, t: 20, b: 25 },
          yaxis: {
            autorange: false,
            range: [1200, 1900]
          },
          xaxis: {
            tickformat: '%Y-%m-%d'
          }
        },
        data: [{
          x: ['2022-01-01', '2022-01-02', '2022-01-03', '2022-01-04', '2022-01-05', '2022-01-06'],
          y: [1450, 1550, 1520, 1500, 1510, 1450],
          name: '자사 주유소',
          marker: {
            color: 'rgba(0,153,153,1)',
            line: {
              color: 'rgba(0,153,153,1)',
              width: 0.5
            }
          },
          text: [1450, 1550, 1520, 1500, 1510, 1450],
          textfont: {
            family: 'Spoqa Han Sans Neo',
            size: 12,
            color: ['rgba(0,153,153,1)', 'rgba(0,23,3,1)', 'rgba(0,153,253,1)', 'rgba(0,153,23,1)', 'rgba(0,1,153,1)']
          },
          textposition: 'top',
          type: 'scatter',
          mode: 'lines+markers+text'
        },
        {
          x: ['2022-01-01', '2022-01-02', '2022-01-03', '2022-01-04', '2022-01-05', '2022-01-06'],
          y: [1420, 1520, 1580, 1600, 1520, 1650],
          name: '경쟁 주유소',
          marker: {
            color: 'rgba(255, 50, 50, 1)',
            line: {
              color: 'rgba(255, 50, 50, 1)',
              width: 0.5
            }
          },
          text: [1420, 1520, 1580, 1600, 1520, 1650],
          textfont: {
            family: 'Spoqa Han Sans Neo',
            size: 12,
            color: 'rgba(255, 50, 50, 1)'
          },
          textposition: 'top',
          mode: 'lines+markers+text'
        }]
      }
    }
  },
  mounted () {
    this.graphShow = true
  }
}
</script> -->
