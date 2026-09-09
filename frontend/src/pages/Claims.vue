<template>
  <div class="max-w-5xl mx-auto py-8 px-4 space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-semibold">My Claims</h1>
      <div class="flex gap-2">
        <Button @click="$router.push('/')">Dashboard</Button>
        <Button appearance="primary" @click="$router.push('/claims/new')">Intimate Claim</Button>
      </div>
    </div>

    <div v-if="$resources.claims.loading" class="text-gray-500">Loading…</div>
    <div class="bg-white border rounded-lg divide-y" v-else>
      <div v-for="c in $resources.claims.data || []" :key="c.name" class="p-4 flex justify-between items-center">
        <div>
          <div class="font-medium">{{ c.claim_number }}</div>
          <div class="text-sm text-gray-500">
            {{ c.claim_type }} · {{ c.incident_date }} · {{ c.claimed_amount }}
          </div>
        </div>
        <span class="text-xs px-2 py-1 rounded-full bg-gray-100">{{ c.status }}</span>
      </div>
      <div v-if="!($resources.claims.data || []).length" class="p-6 text-gray-500 text-sm">No claims yet.</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Claims',
  resources: {
    claims: {
      url: 'insurance_core.portal.portal_list_claims',
      auto: true,
    },
  },
}
</script>
