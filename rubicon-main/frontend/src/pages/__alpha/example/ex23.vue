<template>
  <v-container fluid class="pa-4 ma-0" :style="{ background: $vuetify.theme.themes.light.background }">
  <div style="font-weight: 800;">테이블 내 custom fields 생성</div>
  <div>1. customFields 정의 </div>
  <div>2. alpha-data"-table-view 에 '필드이름_custom' 으로 v-slot 생성</div>
  <div class="pb-4"></div>
  <alphaDataTable :alphaModel="ex12">
    <template v-slot:custom-header>
      <thead>
        <tr>
          <th class="accent white--text text-center" rowspan="2"> 이름 </th>
          <th class="accent white--text text-center" colspan="2" style="border-left:1px solid #ffffff !important;"> 종합정보 </th>
          <th class="accent white--text text-center" colspan="2" style="border-left:1px solid #ffffff !important;"> 개별정보 </th>
          <th class="accent white--text text-center" rowspan="2" style="border-left:1px solid #ffffff !important;"> Action </th>
        </tr>
        <tr>
          <th class="accent white--text text-center" style="border-left:1px solid #ffffff !important;"> Notes </th>
          <th class="accent white--text text-center" > Category </th>
          <th class="accent white--text text-center"  style="border-left:1px solid #ffffff !important;"> calory </th>
          <th class="accent white--text text-center" > Likeing </th>
        </tr>
      </thead>
    </template>
    <template v-slot:calory_custom="{ item }">
      <div> {{ getCommaFormat(item.calory) }} cal</div>
    </template>
    <template v-slot:likeing_custom="{ item }">
      <div v-html="getHTML (item.likeing)"></div>
    </template>
  </alphaDataTable>
  <v-divider></v-divider>
  <alphaDataTable-view :alphaModel="ex12">
    <template v-slot:custom-header>
      <thead>
        <tr>
          <th class="accent white--text text-center" rowspan="2"> 이름 </th>
          <th class="accent white--text text-center" colspan="2" style="border-left:1px solid #ffffff !important;"> 종합정보 </th>
          <th class="accent white--text text-center" colspan="2" style="border-left:1px solid #ffffff !important;"> 개별정보 </th>
          <th class="accent white--text text-center" rowspan="2" style="border-left:1px solid #ffffff !important;"> Action </th>
        </tr>
        <tr>
          <th class="accent white--text text-center" style="border-left:1px solid #ffffff !important;"> Notes </th>
          <th class="accent white--text text-center" > Category </th>
          <th class="accent white--text text-center"  style="border-left:1px solid #ffffff !important;"> calory </th>
          <th class="accent white--text text-center" > Likeing </th>
        </tr>
      </thead>
    </template>
    <template v-slot:calory_custom="{ item }">
      <div> {{ getCommaFormat(item.calory) }} cal</div>
    </template>
    <template v-slot:likeing_custom="{ item }">
      <div v-html="getHTML(item.likeing)"></div>
    </template>
  </alphaDataTable-view>
  </v-container>
</template>

<script>
import alphaDataTable from '@/components/alpha/alphaDataTable'
import alphaDataTableView from '@/components/alpha/alphaDataTableView'
import { alphaExample } from '@/_services'
import { numberWithCommas, floatToFixed } from '@/_helpers'
export default {
  name: 'ex12',
  components: { alphaDataTable, alphaDataTableView },
  data () {
    return {
      ex12: {
        name: 'ex12',
        function: alphaExample.ex12.ex12Function,
        crud: [false, true, false, false],
        customHeader: true,
        headerId: 'ca84889e-de87-4757-b2b2-a9fd3c5635db',
        pagination: true,
        customFields: ['calory', 'likeing']
      }
    }
  },
  methods: {
    getHTML (value) {
      if (value === false) {
        return '<div class="blue--text font-weight-bold"> ▼ ' + value + '</div>'
      } else {
        return '<div class="red--text font-weight-bold"> ▲ ' + value + '</div>'
      }
    },
    getCommaFormat (value) {
      return numberWithCommas(floatToFixed(value))
    }
  }
}
</script>
