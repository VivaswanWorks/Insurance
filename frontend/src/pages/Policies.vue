<template>
  <div class="max-w-5xl mx-auto py-8 px-4 space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold">My Policies</h1>
      <Button @click="$router.push('/')">Dashboard</Button>
    </div>

    <div v-if="$resources.policies.loading" class="text-gray-500">Loading…</div>
    <div class="bg-white border rounded-lg divide-y" v-else>
      <div
        v-for="p in $resources.policies.data || []"
        :key="p.name"
        class="p-4 flex flex-wrap gap-4 justify-between items-center hover:bg-gray-50 cursor-pointer"
        @click="$router.push(`/policies/${p.name}`)">
        <div>
          <div class="font-medium">{{ p.policy_number }}</div>
          <div class="text-sm text-gray-500">
            {{ p.scheme }} · {{ p.start_date }} → {{ p.end_date }}
          </div>
        </div>
        <div class="text-right">
          <div class="text-sm">Sum assured: {{ p.sum_assured }}</div>
          <div class="text-sm text-gray-500">Premium: {{ p.total_premium }}</div>
        </div>
        <span class="text-xs px-2 py-1 rounded-full bg-gray-100">{{ p.status }}</span>
      </div>
      <div v-if="!($resources.policies.data || []).length" class="p-6 text-gray-500 text-sm">
        You have no policies.
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Policies',
  resources: {
    policies: {
      url: 'insurance_core.portal.portal_list_policies',
      auto: true,
    },
  },
}
</script>
