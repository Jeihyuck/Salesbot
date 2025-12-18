<template>
  <div>
    <v-list>
      <template v-for="item in items" :key="item.id">
      <v-list-group v-if="item.children && item.children.length">
        <template v-slot:activator="{ props }">
          <v-list-item
            v-bind="props"
            :key="item.id"
            :prepend-icon="item.icon"
            :title="item.name"
          ></v-list-item>
        </template>
        <v-list-item class="sub-menu-item"  density="compact"
          v-for="subItem in item.children"
          :key="item.id"
          :title="subItem.name"
          :value="subItem.name"
          link @click="$router.push(subItem.url)"
        ></v-list-item>
      </v-list-group>
      <v-list-item
        v-else
        :prepend-icon="item.icon"
        :title="item.name"
        link
        @click="$router.push(item.url)"
      >
      </v-list-item>
      </template>
    </v-list>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const open = ref(['Users']);

const props = defineProps({
  items: {
    type: Array,
    required: true,
  },
});

const activeGroups = ref([]);
const router = useRouter();

function navigate(url) {
  // console.log(url)
  if (url) {
    router.push(url);
  }
}
</script>
