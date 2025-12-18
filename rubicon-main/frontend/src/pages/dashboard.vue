<template>
  <v-col class="pb-6" style="height: calc(100vh - 72px); overflow-y: auto;">
    <v-row><v-btn @click="test()">TEST</v-btn></v-row>
    <v-row>
      <v-col cols="6" class="pr-1">
        <alphaChartApex ref="apiCountFromChannelsRef" :alphaModel="apiCountFromChannels" />
      </v-col>
      <v-col cols="3" class="pr-1">
        <alphaChartApex :alphaModel="thumbUpDown" />
      </v-col>
      <v-col cols="3" class="pr-3">
        <alphaChartApex :alphaModel="successFail" />
      </v-col>
    </v-row>
    <v-row class="pt-0 mt-1">
      <v-col cols="12" class="pr-3">
        <alphaChartApex :alphaModel="thumbDownDetails" />
      </v-col>
    </v-row>
    <v-row class="pt-0 mt-1">
      <v-col cols="12" class="pr-3">
        <alphaChartApex ref="intelligenceStatusRef" :alphaModel="intelligenceStatus" />
      </v-col>
    </v-row>
    <v-row class="pt-0 mt-1">
      <v-col cols="12" class="pr-3">
        <alphaChartApex :alphaModel="responseTime" />
      </v-col>
    </v-row>
    <v-row class="pt-0 mt-1">
      <v-col cols="4" class="pr-1">
        <alphaChartApex :alphaModel="modelTokenCount" />
      </v-col>
      <v-col cols="8" class="pr-3">
        <alphaChartApex :alphaModel="moduleTokenCount" />
      </v-col>
    </v-row>
  </v-col>
</template>

<script setup>
import alphaChartApex from '@/components/alpha/alphaChartApex'
import { reactive } from 'vue';
import { rubiconAdmin } from '@/_services';
// import Test from '__alpha_old/test.vue';

const apiCountFromChannelsRef = ref(null)
const intelligenceStatusRef = ref(null)

const test = () => {
  rubiconAdmin.dashboard.status('api_call_count').then((response)=> {
    console.log(response.data)
    apiCountFromChannels.chartOptions.xaxis.categories = response.data.channel[0]
    apiCountFromChannels.series[0].data = response.data.channel[1]
    apiCountFromChannelsRef.value.refresh()

    intelligenceStatus.chartOptions.xaxis.categories = response.data.intelligence[0]
    intelligenceStatus.series[0].data = response.data.intelligence[1]
    intelligenceStatusRef.value.refresh()
  })
}

const apiCountFromChannels = reactive({
  type: "bar",
  height: 300,
  series: [{
    name: "Sales",
    data: []
  }],
  chartOptions: {
    dataLabels: {
      offsetY: -20
    },
    xaxis: {
      categories: [],
      title: {
        text: "Channel"
      }
    },
    yaxis: {
      title: {
        text: "Count"
      }
    },
    title: {
      text: 'API Call Count From Channels', // Title text
    },
  },
})

const thumbDownDetails = reactive({
  type: "bar",
  height: 300,
  series: [{
    name: "Count",
    data: [30, 40, 45, 50, 49, 60, 70, 91]
  }],
  chartOptions: {
    dataLabels: {
      offsetY: -20
    },
    xaxis: {
      categories: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
      title: {
        text: "Thumb Down Items"
      }
    },
    yaxis: {
      title: {
        text: "Count"
      }
    },
    title: {
      text: 'Thumb Down Details', // Title text
    },
  },
})


const intelligenceStatus = reactive({
  type: "bar",
  height: 300,
  series: [{
    name: "Count",
    data: []
  },
  {
    name: "thumb down",
    data: []
  },
  {
    name: "Inaccurate",
    data: []
  }],
  chartOptions: {
    colors: ["#008FFB", "#FEB019", "#FF4560"],
    dataLabels: {
      offsetY: -20
    },
    xaxis: {
      categories: [],
      title: {
        text: "intelligence"
      }
    },
    yaxis: {
      title: {
        text: "Count"
      }
    },
    title: {
      text: 'Performance for each Intelligence', // Title text
    },
  },
})


const thumbUpDown = reactive({
  type: "donut",
  height: 300,
  series: [144, 22, 13],
  chartOptions: {
    labels: ["N/A", "Thumb Up", "Thumb Down"],
    colors: ["#775DD0", "#008FFB", "#FF4560"],
    dataLabels: {
      formatter: function (val, opts) {
        return opts.w.globals.labels[opts.seriesIndex] + ": " + val.toFixed(2) + "%";
      },
    },
    plotOptions: {
      pie: {
        donut: {
          size: '50%',
          labels: {
            show: true,
            name: {
              show: true,
              fontSize: '16px',
              fontWeight: 600,
              color: '#fff',
            },
            value: {
              show: true,
              fontSize: '14px',
              fontWeight: 400,
              color: '#fff',
              formatter: (val) => `${val.toFixed}%`, // Display percentage values
            },
          },
        },
      },
    },
    title: {
      text: 'Thumb Up / Down', // Title text
    },
    stroke: {
      width: 2,            // Width of the border line
      colors: ['#212121'],    // Color of the border line
    },
  },
})

const successFail = reactive({
  type: "donut",
  height: 300,
  series: [144, 13],
  chartOptions: {
    labels: ["Success", "Fail"],
    colors: ["#008FFB", "#FF4560"],
    dataLabels: {
      formatter: function (val, opts) {
        return opts.w.globals.labels[opts.seriesIndex] + ": " + val.toFixed(2) + "%";
      },
    },
    plotOptions: {
      pie: {
        donut: {
          size: '50%',
          labels: {
            show: true,
            name: {
              show: true,
              fontSize: '16px',
              fontWeight: 600,
              color: '#fff',
            },
            value: {
              show: true,
              fontSize: '14px',
              fontWeight: 400,
              color: '#fff',
              formatter: (val) => `${val}%`, // Display percentage values
            },
          },
        },
      },
    },
    title: {
      text: 'Success / Fail', // Title text
    },
    stroke: {
      width: 2,            // Width of the border line
      colors: ['#212121'],    // Color of the border line
    },
  },
})


const responseTime = reactive({
  type: "bar",
  height: 300,
  series: [{
    name: "Max Response Time",
    data: [60, 40, 54, 65, 59, 70, 80, 121]
  },
  {
    name: "Avg Response Time",
    data: [30, 40, 45, 50, 49, 60, 70, 91]
  },
  {
    name: "Min Response Time",
    data: [10, 20, 35, 40, 39, 50, 60, 71]
  }],
  chartOptions: {
    dataLabels: {
      offsetY: -20
    },
    xaxis: {
      categories: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
      title: {
        text: "Module"
      }
    },
    yaxis: {
      title: {
        text: "Seconds"
      }
    },
    title: {
      text: 'Response Time (Max, Avg, Min)', // Title text
    },
  },
})

const modelTokenCount = reactive({
  type: "donut",
  height: 300,
  series: [1444553543, 24535342],
  chartOptions: {
    labels: ["GPT-4o-mini", "GPT-4o"],
    colors: ["#775DD0", "#008FFB"],
    dataLabels: {
      formatter: function (value, { dataPointIndex }) {
        return value.toLocaleString();
      }
    },
    plotOptions: {
      pie: {
        donut: {
          size: '50%',
          labels: {
            show: true,
            name: {
              show: true,
              fontSize: '16px',
              fontWeight: 600,
              color: '#fff',
            },
            value: {
              show: true,
              fontSize: '14px',
              fontWeight: 400,
              color: '#fff',
              formatter: (val) => `${val.toFixed}%`, // Display percentage values
            },
          },
        },
      },
    },
    title: {
      text: 'Token Count of GPT Model', // Title text
    },
    stroke: {
      width: 2,            // Width of the border line
      colors: ['#212121'],    // Color of the border line
    },
  },
})

const moduleTokenCount = reactive({
  type: "bar",
  height: 300,
  series: [{
    name: "Count",
    data: [30, 40, 45, 50, 49, 60, 70, 91]
  }],
  chartOptions: {
    dataLabels: {
      offsetY: -20
    },
    xaxis: {
      categories: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"],
      title: {
        text: "Module"
      }
    },
    yaxis: {
      title: {
        text: "Count"
      }
    },
    title: {
      text: 'Token Count of Rubicon Module', // Title text
    },
  },
})

onMounted(() => {
  rubiconAdmin.dashboard.status('api_call_count').then((response)=> {
    // console.log(response.data)
    apiCountFromChannels.chartOptions.xaxis.categories = response.data.channel[0]
    apiCountFromChannels.series[0].data = response.data.channel[1]
    apiCountFromChannelsRef.value.refresh()

    intelligenceStatus.chartOptions.xaxis.categories = response.data.intelligence[0]
    intelligenceStatus.series[0].data = response.data.intelligence[1]
    intelligenceStatusRef.value.refresh()
  })
});
</script>
