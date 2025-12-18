<template>
  <!-- <v-container fluid class="pa-4 ma-0" :style="{ background: $vuetify.theme.themes.light.background }">
    <v-row>
      <v-col cols="4" class="pr-2">
        <alpha-graph-basic :alphaModel="graph1" :show="graphShow"></alpha-graph-basic>
      </v-col>
      <v-col cols="4" class="px-1">
        <alpha-graph-basic :alphaModel="graph2" :show="graphShow"></alpha-graph-basic>
      </v-col>
      <v-col cols="4" class="pl-2">
        <alpha-graph-basic :alphaModel="graph3" :show="graphShow"></alpha-graph-basic>
      </v-col>
    </v-row>
    <v-row class="justify-center">
      <a href="https://plotly.com/javascript/bar-charts/" target="_blank">Plotly Bar Chart Reference</a>
    </v-row>
    <v-row>
      <v-col cols="4">
        <v-card class="ma-0" outlined style="height: 150px"></v-card>
      </v-col>
      <v-col cols="4">
        <v-card class="ma-0" outlined style="height: 150px"></v-card>
      </v-col>
      <v-col cols="4">
        <v-card class="ma-0"  outlined style="height: 150px"></v-card>
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
        sizeInfo: {
          margin: 400,
          stacked: 1
        },
        data: [{
          x: ['giraffes', 'orangutans', 'monkeys'],
          y: [20, 14, 23],
          name: 'SF Zoo',
          type: 'bar'
        }]
      },
      graph2: {
        flat: false,
        sizeInfo: {
          margin: 400, // pixel
          stacked: 1,
          innerPadding: 10
        },
        displayModeBar: true,
        customLayout: {
          showlegend: true,
          barmode: 'group',
          margin: { l: 20, r: 30, t: 20, b: 10 }
        },
        data: [{
          x: ['giraffes', 'orangutans', 'monkeys'],
          y: [20, 14, 23],
          name: 'SF Zoo',
          type: 'bar'
        },
        {
          x: ['giraffes', 'orangutans', 'monkeys'],
          y: [12, 18, 29],
          name: 'LA Zoo',
          type: 'bar'
        }]
      },
      graph3: {
        flat: false,
        sizeInfo: {
          margin: 400, // pixel
          stacked: 1,
          innerPadding: 80
        },
        title: '월 목표 대비 판매량 현황 비교',
        unitInfo: '(단위: 드럼)',
        customLegends: '<div style="width: 10px; height: 10px; background-color: rgba(0,153,153,1);"></div><div class="text-caption ml-1 mr-4">목표</div> <div style="width: 10px; height: 10px; background-color: rgba(0,114,187,1);"></div><div class="text-caption ml-1 mr-4">실적</div> <div style="width: 10px; height: 10px; background-color: #FF850A;"></div><div class="text-caption ml-1 mr-4">예상</div>',
        customLayout: {
          showlegend: false,
          barmode: 'stack',
          margin: { l: 20, r: 30, t: 20, b: 10 },
          yaxis: {
            range: [],
            gridcolor: 'rgb(210, 210, 210)',
            visible: true
          },
          xaxis: {
            range: []
          },
          annotations: [
            {
              x: '전사 목표',
              y: 1200,
              xanchor: 'center',
              yanchor: 'bottom',
              showarrow: false,
              text: '1,200'
            },
            {
              x: '예상 달성률 (실적 + 예상)',
              y: 1120,
              xanchor: 'center',
              yanchor: 'bottom',
              showarrow: false,
              text: '1,120(100)'
            }
          ]
        },
        data: [{
          x: ['전사 목표', '예상 달성률 (실적 + 예상)'],
          y: [1200, 1020],
          width: 0.5,
          marker: {
            color: ['rgba(0,153,153,1)', 'rgba(0,114,187,1)']
          },
          text: ['1,200', '1,020'],
          hovertemplate: '%{text}<extra></extra>',
          textposition: 'top',
          textangle: 0,
          textfont: {
            family: 'Spoqa Han Sans Neo',
            size: 12,
            color: ['rgba(255,255,255,1)', 'rgba(255,255,255,1)']
          },
          type: 'bar'
        },
        {
          x: ['전사 목표', '예상 달성률 (실적 + 예상)'],
          y: [0, 100],
          width: 0.5,
          marker: {
            color: ['rgba(249,158,26,1)', 'rgba(249,158,26,1)']
          },
          text: ['', '100'],
          hovertemplate: '%{text}<extra></extra>',
          textposition: 'top',
          textangle: 0,
          textfont: {
            family: 'Spoqa Han Sans Neo',
            size: 12,
            color: ['rgba(255,255,255,1)', 'rgba(255,255,255,1)']
          },
          type: 'bar'
        }]
      }
    }
  },
  mounted () {
    this.graphShow = true
  }
}
</script> -->
