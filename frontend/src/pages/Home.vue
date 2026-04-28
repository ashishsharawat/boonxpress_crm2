<template>
  <div class="h-full">
    <component :is="verticalHome" v-if="verticalHome" />
    <div v-else class="flex items-center justify-center h-full">
      <div class="w-6 h-6 border-2 border-boon-primary border-t-transparent rounded-full animate-spin" />
    </div>
  </div>
</template>

<script setup>
import { shallowRef, onMounted } from 'vue'
import { useVertical } from '@/composables/useVertical'

const { homeComponent } = useVertical()
const verticalHome = shallowRef(null)

const componentMap = {
  SalonHome: () => import('@/verticals/salon/SalonHome.vue'),
  ClinicHome: () => import('@/verticals/clinic/ClinicHome.vue'),
  AutoHome: () => import('@/verticals/auto/AutoHome.vue'),
  RetailHome: () => import('@/verticals/retail/RetailHome.vue'),
  MedSpaHome: () => import('@/verticals/medspa/MedSpaHome.vue'),
  UsedCarHome: () => import('@/verticals/usedcar/UsedCarHome.vue'),
  CourseHome: () => import('@/verticals/course/CourseHome.vue'),
}

onMounted(async () => {
  const loader = componentMap[homeComponent.value]
  if (loader) {
    const mod = await loader()
    verticalHome.value = mod.default
  }
})
</script>
