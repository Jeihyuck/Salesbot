<template>
  <v-navigation-drawer :width="220" v-if="drawer" :style="{ background: $vuetify.theme.themes.light.grayDarkened1 }" clipped v-model="drawer" app>
    <v-expansion-panels class="condensed mt-2" flat focusable tile>
      <v-expansion-panel
        v-for="(item,i) in menuItems"
        :key="i"  class="pa-0 ma-0"
      >
        <v-expansion-panel-header class="pr-3 pl-5 font-weight-medium" :style="{ background: $vuetify.theme.themes.light.grayDarkened1 }" :hide-actions="!item.group">
          <template v-slot:actions>
            <v-icon :style="{ color: $vuetify.theme.themes.light.grayText }" >
              $expand
            </v-icon>
          </template>
          <router-link v-if="!item.group" :to="{ name: 'service', params: { serviceName: item.serviceName }, query: item.serviceQuery }" style="text-decoration: none; color: inherit;">
            <div :style="{ color: $vuetify.theme.themes.light.grayText }">
              {{item.menuName}}
            </div>
          </router-link>
          <div v-if="item.group" :style="{ color: $vuetify.theme.themes.light.grayText }">
            {{item.menuName}}
          </div>
        </v-expansion-panel-header>
        <v-expansion-panel-content v-if="item.group" :style="{ background: $vuetify.theme.themes.light.grayDarkened1 }">
          <div v-for="subItem in item.subItems" :key="subItem.title">
            <router-link  :to="{ name: 'service', params: { serviceName: subItem.serviceName }, query: subItem.serviceQuery }" style="text-decoration: none; color: inherit;">
              <v-list-item dense class="pa-0 ma-0">
                <v-list-item-content class="px-0">
                  <v-list-item-title :class="'d-flex justify-space-between pa-0 text-subtitle-2' + selectedStyle(subItem)" :style="{ color: $vuetify.theme.themes.light.grayText }">
                    {{ subItem.menuName }}
                  </v-list-item-title>
                </v-list-item-content>
              </v-list-item>
            </router-link>
          </div>
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-expansion-panels>
  </v-navigation-drawer>
</template>

<script>
import alphaNavigationDrawerPlugIn from '@/plugins/alphaNavigationDrawer.plugin'

export default {
  name: 'alphaNavigationDrawer',
  props: ['menuItems'],
  data () {
    return {
      include_navbar_search: null,
      activeTitle: null,
      drawer: null,
      current: window.location.pathname
    }
  },
  watch: {
    $route () {
      this.current = window.location.pathname
    }
  },
  methods: {
    selectedStyle (item) {
      if (item.category) {
        return this.current.split('/')[this.current.split('/').length - 1] === item.serviceName && item.serviceQuery.category === this.$route.query.category
          ? ' current'
          : ''
      } else {
        return this.current.split('/')[this.current.split('/').length - 1] === item.serviceName
          ? ' current'
          : ''
      }
    },
    selectItem (itemTitle) {
      this.activeTitle = itemTitle
    },
    showNavigationDrawer () { this.drawer = true },
    hideNavigationDrawer () { this.drawer = false },
    toggleNavigationDrawer () { this.drawer = !this.drawer }
  },
  beforeMount () {
    alphaNavigationDrawerPlugIn.EventBus.$on('showNavigationDrawer', () => {
      this.showNavigationDrawer()
    })
    alphaNavigationDrawerPlugIn.EventBus.$on('hideNavigationDrawer', () => {
      this.hideNavigationDrawer()
    })
    alphaNavigationDrawerPlugIn.EventBus.$on('toggleNavigationDrawer', () => {
      this.toggleNavigationDrawer()
    })
  }
}
</script>

<style scoped lang="sass">
  @import '~@/alphaColors.scss'

  .v-expansion-panels
    .v-expansion-panel-header
      padding-top: 16px
      padding-bottom: 16px
      // height: 50px !important
      min-height: unset !important

      div
        font-size: 16px !important
        font-weight: bold

      &.v-expansion-panel-header--active
        background-color: $grayDarkened2 !important
        color: grayTextBrightend !important
        div span
          color: grayTextBrightend !important
        // &:before
        //   opacity: 0 !important

      &:not(.v-expansion-panel-header--active)
        background-color: $grayDarkened1 !important

    .v-expansion-panel.v-expansion-panel--active
      .v-expansion-panel-content
        padding: 20px 36px !important
        background-color: $gray
        &::v-deep .v-expansion-panel-content__wrap
          padding: 0 !important
          div:nth-child(n+2)
            margin-top: 24px
          .v-list-item--dense
            min-height: unset
            .v-list-item__content
              padding: 0 !important
              .v-list-item__title
                font-size: 14px !important
                font-weight: bold
                &.current
                  font-size: 15px !important
                  font-weight: bold
                  color: $white !important
</style>
