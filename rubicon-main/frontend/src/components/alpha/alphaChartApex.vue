<template>
  <v-container fluid class="ma-0 pa-0" :key="componentKey" >
    <v-card class="px-3 pt-3" :height="props.alphaModel.height">
      <resize-observer @notify="handleResize"/>
      <VueApexCharts ref="chart" :options="props.alphaModel.chartOptions" :type="props.alphaModel.type" :series="props.alphaModel.series" :height="props.alphaModel.height - 20"/>
    </v-card>
  </v-container>
</template>

<script setup>

import { ref, onMounted } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import merge from 'lodash.merge'
import 'vue3-resize/dist/vue3-resize.css'

const componentKey = ref(0);

const props = defineProps({
  alphaModel: Object
})


const handleResize = ({ width, height }) => {
  console.log('resized', width, height)
  componentKey.value += 1;
};



const refresh = () => {
  console.log('refresh')
  componentKey.value += 1;
};

defineExpose({
  refresh
})


const chartOptionsBase = ref({
  chart: {
    background: '#212121',
    padding: {
      top: 0,
      right: 0,
      bottom: 0,
      left: 0,
    },
    toolbar: {
      show: false, // Show the toolbar
    },
    events: {
      dataPointSelection: function (event, chartContext, config) {
        const clickedLabel = config.w.globals.labels[config.dataPointIndex];
        const clickedValue = config.w.config.series[config.dataPointIndex];
        console.log(`You clicked on ${clickedLabel}: ${clickedValue}`);
      }
    },
  },
  theme: {
    mode: "dark", // Dark mode setting
  },
  legend: {
    show: false, // Hide the legend
    position: "bottom",
    labels: {
      colors: "#fff", // White color for legend labels
    },
  },
  dataLabels: {
    style: {
      colors: ["#fff"], // White color for data labels
    },
  },
  plotOptions: {
    bar: {
      dataLabels: {
        position: 'top'
      }
    },
  },
  title: {
    align: 'center',
    margin: 10,                       // Margin at the top of the chart
    offsetY: 15,                       // Offset Y position of the title
    style: {
      fontSize: '0.8em',
      color: '#ffffff',
    },
  },
  grid: {
    borderColor: "#424242",
  },
  xaxis: {
    title: {
      style: {
        color: '#ffffff',
      },
    },
    labels: {
      style: {
        colors: '#ffffff',
      },
    },
  },
  yaxis: {
    title: {
      style: {
        color: '#ffffff',
      },
    },
    labels: {
      style: {
        colors: '#ffffff',
      },
    },
  },
  theme: {
    palette: 'palette1',
    mode: 'dark',
  },
})

onMounted(() => {
  props.alphaModel.chartOptions = merge(props.alphaModel.chartOptions, chartOptionsBase.value);
  componentKey.value += 1;
});
</script>
