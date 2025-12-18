<template>
  <apexchart type="line" :options="chartOptions" :series="series" />
</template>

<script>
import { defineComponent, ref } from 'vue';
import VueApexCharts from 'vue3-apexcharts';

export default defineComponent({
  name: 'LineChart',
  components: {
    apexchart: VueApexCharts,
  },
  setup() {
    const series = ref([
      {
        name: 'Sales',
        data: [10, 41, 35, 51, 49, 62, 69, 91, 148],
      },
    ]);

    const chartOptions = ref({
      chart: {
        height: 350,
        type: 'line',
      },
      stroke: {
        curve: 'smooth',
      },
      title: {
        text: 'Product Sales Over Time',
        align: 'left',
      },
      xaxis: {
        categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'],
      },
    });

    return {
      series,
      chartOptions,
    };
  },
});
</script>

<style scoped>
/* Add any specific styles for the chart here */
</style>
