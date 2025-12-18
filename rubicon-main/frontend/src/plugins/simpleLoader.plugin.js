import SimpleLoader from '@/components/basic/SimpleLoader.vue'

const simpleLoaderPlugIn = {
  install (Vue, options) {
    this.EventBus = new Vue()
    Vue.component('simple-loader', SimpleLoader)

    Vue.prototype.$simpleLoaderPlugIn = {
      show () {
        simpleLoaderPlugIn.EventBus.$emit('show')
      },
      hide () {
        simpleLoaderPlugIn.EventBus.$emit('hide')
      }
    }
  }
}

export default simpleLoaderPlugIn
