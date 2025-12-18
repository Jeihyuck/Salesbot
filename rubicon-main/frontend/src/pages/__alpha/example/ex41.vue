<template>
</template>
<!-- <template>
  <v-container fluid class="pa-4 ma-0" :style="{ background: $vuetify.theme.themes.light.background }">
    <div ref="container"></div>
  </v-container>
</template>

<script>
import * as THREE from 'three'

export default {
  name: 'ex41',
  data () {
    return {
    }
  },
  mounted () {
    const container = this.$refs.container
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    )
    const renderer = new THREE.WebGLRenderer()
    renderer.setSize(window.innerWidth, window.innerHeight)
    container.appendChild(renderer.domElement)
    const box = new THREE.BoxGeometry(10, 10, 10)
    const material = new THREE.MeshBasicMaterial({ color: 0xffffff })
    const mesh = new THREE.Mesh(box, material)
    scene.add(mesh)
    camera.position.z = 30

    const animate = () => {
      requestAnimationFrame(animate)
      mesh.rotation.x += 0.01
      mesh.rotation.y += 0.01
      renderer.render(scene, camera)
    }
    animate()
  }
}
</script> -->
