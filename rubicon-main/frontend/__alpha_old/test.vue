<template>
  <v-container fluid class="px-0 mt-0 pt-0">
    <alphaTab :items="items" />
  </v-container>
</template>

<script>
import alphaTab from '@/components/alpha/alphaTab'
import testLogin from '@/pages/__alpha/test/testLogin'
import apiTest from '@/pages/__alpha/test/apiTest'
// import backendTest from '@/pages/__alpha/test/backendTest'
// import codeTest from '@/pages/__alpha/test/codeTest'
// import sqlTest from '@/pages/__alpha/test/sqlTest'

export default {
  name: 'alphaTest',
  components: {
    alphaTabBar
  },
  data () {
    return {
      items: [
        { tab: 'Login For Test', components: testLogin },
        { tab: 'API Test', components: apiTest },
        // { tab: 'Backend Test', components: backendTest },
        // { tab: 'Code Test', components: codeTest }
      ]
    }
  }
}
</script>

<style scoped>
  #mainPage {
    height: calc(100vh - 230px);
  }
</style>
