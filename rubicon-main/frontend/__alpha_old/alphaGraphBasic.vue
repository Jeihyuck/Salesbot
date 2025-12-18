<template>
  <v-container fluid class="ma-0 pa-0">
  <resize-observer @notify="handleResize" />
  <div v-show="show" class="ma-0 pa-0">
    <v-card ref="alphaGraphBasic" :flat="alphaModel.flat" :class="graphCardClass" :height="ySize">
      <v-card-title v-if="alphaModel.title" class="pt-2 justify-center font-weight-bold subtitle-1 py-2"> {{ alphaModel.title }} <div style="padding-top: 2px;" class="text-caption"> &nbsp;{{alphaModel.unitInfo}} </div> </v-card-title>
      <div v-if="alphaModel.customLegends" class="mx-6 mt-2 d-flex justify-end align-center" v-html="alphaModel.customLegends"></div>
      <v-img class="pa-0 ma-0">
        <div class="pa-0 ma-0" :id="id"></div>
      </v-img>
    </v-card>
  </div>
  <div v-show="!show" class="ma-0 pa-0">
    <v-card :flat="alphaModel.flat" :height="ySize">
      <v-card-text class="d-flex justify-center fill-height">
        <div class="align-self-center"> 그래프의 데이터가 준비되지 않았습니다. 조건 설정 후 '조회' 버튼을 눌러주세요.</div>
      </v-card-text>
    </v-card>
  </div>
  </v-container>
</template>

<script>
import { uuid } from 'vue-uuid'
import merge from 'lodash/merge'
import 'vue-resize/dist/vue-resize.css'
import { ResizeObserver } from 'vue-resize'

const Plotly = require('plotly.js-basic-dist-min')

export default {
  components: {
    ResizeObserver
  },
  props: ['alphaModel', 'show'],
  data () {
    return {
      ySize: null,
      id: uuid.v4(),
      spaceBetweenGraph: 30,
      clickPoint: null,
      graphElement: null,
      baseLayout: {
        initializaed: false,
        margin: { l: 20, r: 20, t: 20, b: 27 },
        autosize: true,
        modebar: {
          // vertical modebar button layout
          orientation: 'v',
          // for demonstration purposes
          bgcolor: 'white',
          color: 'black',
          activecolor: '#9ED3CD'
        },
        legend: {
          orientation: 'h',
          yanchor: 'top',
          y: 1.15,
          xanchor: 'right',
          x: 0.958
        },
        legend_font: {
          family: 'Spoqa Han Sans Neo',
          size: 10,
          color: 'rgb(0, 0, 0)'
        },
        hoverlabel_font: {
          family: 'Spoqa Han Sans Neo',
          size: 10,
          color: 'rgb(0, 0, 0)'
        },
        xaxis_tickangle: 8,
        plot_bgcolor: '#ffffff',
        xaxis: {
          // autorange: false,
          // range: ['2022-05-01 00:00:00', '2022-05-01 06:00:00'],
          showline: true,
          showgrid: false,
          showticklabels: true,
          linecolor: 'rgb(80, 80, 80)',
          linewidth: 1,
          ticks: 'inside',
          ticklen: 0,
          tickfont: {
            family: 'Spoqa Han Sans Neo',
            size: 10,
            color: 'rgb(0, 0, 0)'
          },
          position: 0
        },
        yaxis: {
          automargin: true,
          autorange: true,
          titlefont: {
            family: 'Spoqa Han Sans Neo',
            size: 10,
            weight: 900,
            color: 'rgb(107, 107, 107)'
          },
          showline: true,
          showgrid: true,
          gridcolor: 'rgb(210, 210, 210)',
          gridwidth: 1,
          showticklabels: true,
          linecolor: 'rgb(0, 0, 0)',
          linewidth: 0,
          ticks: 'outside',
          ticklen: 1,
          tickfont: {
            family: 'Spoqa Han Sans Neo',
            size: 10,
            weight: 900,
            color: 'rgb(0, 0, 0)'
          }
        }
      }
    }
  },
  asyncComputed: {
    graphCardClass () {
      if (this.alphaModel.flat) {
        return 'pa-0 my-1 mx-0'
      } else {
        return 'elevation-1 pa-0 my-1 mx-0'
      }
    }
  },
  watch: {
    'alphaModel.data': {
      deep: true,
      handler () {
        this.refresh()
      }
    }
  },
  methods: {
    async graphHeightResize (height) {
      if (this.alphaModel.sizeInfo && this.alphaModel.layout) {
        const totalSpace = height - this.alphaModel.sizeInfo.margin
        this.ySize = String((totalSpace / this.alphaModel.sizeInfo.stacked)) + 'px'

        let graphHeight = 0
        if (this.alphaModel.sizeInfo.innerPadding) {
          graphHeight = (totalSpace / this.alphaModel.sizeInfo.stacked) - this.alphaModel.sizeInfo.innerPadding
        } else {
          graphHeight = (totalSpace / this.alphaModel.sizeInfo.stacked)
        }
        this.$set(this.alphaModel.layout, 'height', graphHeight)
      }
    },
    handleResize ({ width, height }) { // eslint-disable-line @typescript-eslint/no-unused-vars
      this.graphHeightResize(height)
      this.refresh()
    },
    async refresh () {
      await this.graphHeightResize(document.documentElement.clientHeight)
      merge(this.alphaModel.layout, this.alphaModel.customLayout)
      if (!this.graphElement) {
        this.graphElement = document.getElementById(this.id)
      }
      Plotly.react(this.graphElement, this.alphaModel.data, this.alphaModel.layout, {
        displayModeBar: this.alphaModel.displayModeBar,
        modeBarButtonsToRemove: ['sendDataToCloud', 'select2d', 'lasso2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian'],
        displaylogo: false
      })
    }
    // animate () {
    //   Plotly.animate(this.graphElement, {
    //     data: [{ y: this.alphaModel.data.y.data }],
    //     traces: [0],
    //     layout: {}
    //   }, {
    //     transition: {
    //       duration: 300,
    //       easing: 'cubic-in-out'
    //     },
    //     frame: {
    //       duration: 300
    //     }
    //   })
    // }
  },
  async mounted () {
    this.alphaModel.layout = this.baseLayout
    if (this.alphaModel.customLegends !== undefined) {
      this.$set(this.alphaModel.layout, 'showlegend', false)
    }
    await this.refresh()
    this.graphElement.on('plotly_click', function (data) {
      this.$emit('clickGraph', data.points[0].x, data.points[0].y)
    }.bind(this))
  }
}
</script>

<style scoped>
g.draglayer.cursor-crosshair {
  padding: 5px;
}
</style>
