<template>
  <v-app id="test-page">
    <v-main class="pa-0 ma-0">
    <v-container fluid class="px-0 mt-0 pt-0">
      <v-list three-line>
      <template v-for="(item, index) in examples">
        <v-subheader
          v-if="item.header"
          :key="item.header"
          v-text="item.header"
        ></v-subheader>

        <v-divider
          v-else-if="item.divider"
          :key="index"
          :inset="item.inset"
        ></v-divider>

        <v-list-item
          v-else
        >
          <v-list-item-content class="py-0">
            <v-list-item-title v-html="item.title"></v-list-item-title>
            <v-list-item-subtitle style="margin-top: -40px !important;" v-html="item.description"></v-list-item-subtitle>
          </v-list-item-content>
        </v-list-item>
      </template>
    </v-list>
    </v-container>
    </v-main>
  </v-app>
</template>

<script lang='ts'>
export default {
  name: 'exList',
  data () {
    return {
      selectedExample: null,
      examples: [
        { header: 'SIMPLE EXAMPLES' },
        { title: 'EX 01 : VUE #1', description: 'data / v-model' },
        { title: 'EX 02 : VUE #2', description: 'method' },
        { title: 'EX 03 : VUE #3', description: 'watch / computed' },
        { title: 'EX 04 : VUE #4', description: 'dialog' },
        { title: 'EX 05 : VUE #5', description: 'communication between components (prop / emit / sync / call child component function)' },
        { divider: true, inset: false },
        { header: 'VUETIFY' },
        { title: 'EX 11 : ', description: 'alignment' },
        { divider: true, inset: false },
        { header: 'FILTER AND TABLES' },
        { title: 'EX 21 : Filter', description: '' },
        { title: 'EX 22 : Table : Data table #1', description: 'Simple without filter, with annotation of foreign key value(backend), data map(frontend), without pagination' },
        { title: 'EX 23 : Table : Data table #2', description: 'Simple without filter, customized header, customized field' },
        { title: 'EX 24 : Table : Data table #3', description: 'Simple with filter' },
        { title: 'EX 25 : Table : Data table #4', description: 'Simple with filter, create, delete, update, and custom buttons' },
        { title: 'EX 26 : Table : Data table #5', description: 'Table filter, fullLoad, pagination' },
        { title: 'EX 27 : Table : Data table #6', description: 'Excel Download, Upload' },
        // Table sorting can be set on table admin page. to run pagination fullLoad should be true
        // { title: 'EX 28 : Table : Data table #7', description: 'Multi Select' },
        { divider: true, inset: false },
        { header: 'GRAPH' },
        { title: 'EX 31 : Graph : Bar Chart', description: '' },
        { title: 'EX 32 : Graph : Line Chart', description: '' },
        { title: 'EX 33 : Graph : Scatter Chart', description: '' },
        { title: 'EX 34 : Graph : Band Chart', description: '' },
        { title: 'EX 35 : Graph : Box Plot', description: '' },
        { title: 'EX 39 : Graph : Map', description: '' },
        { divider: true, inset: false },
        { header: '3D' },
        { title: 'EX 41 : Three : Rotating cuboid shape', description: '' },
        { title: 'EX 42 : Three : Animation', description: '' },
        { divider: true, inset: false },
        { header: 'MISC' },
        { title: 'EX 91 : Tab', description: '' },
        { title: 'EX 92 : File Upload', description: '' },
        { title: 'EX 93 : Excel Download', description: '' },
        { title: 'EX 94 : Page Move #1', description: 'From' },
        { title: 'EX 95 : Page Move #2', description: 'To' },
        { title: 'EX 96 : Overlay', description: 'To' },
        { title: 'EX 97 : Confirm', description: 'To' },
        { title: 'EX 98 : Notification', description: 'To' },
        { title: 'EX 99 : GraphQL', description: '' },
        { title: 'EX 100 : Channel', description: '' },
        { divider: true, inset: false }
      ]
    }
  }
}
</script>

<style scoped>

</style>
