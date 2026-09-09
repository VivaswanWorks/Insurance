<template>
  <div class="min-h-screen bg-gray-50 text-gray-900">
    <nav class="bg-white border-b sticky top-0 z-10">
      <div class="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
        <router-link to="/" class="font-semibold text-lg tracking-tight text-gray-900 no-underline">
          Insurance Portal
        </router-link>
        <div class="flex items-center gap-1 text-sm">
          <router-link
            v-for="item in nav"
            :key="item.to"
            :to="item.to"
            class="px-3 py-1.5 rounded-md text-gray-600 hover:bg-gray-100 hover:text-gray-900 no-underline"
            active-class="bg-gray-100 text-gray-900 font-medium">
            {{ item.label }}
          </router-link>
        </div>
      </div>
    </nav>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      nav: [
        { to: '/', label: 'Dashboard' },
        { to: '/policies', label: 'Policies' },
        { to: '/claims', label: 'Claims' },
        { to: '/claims/new', label: 'New Claim' },
      ],
    }
  },
}
</script>
