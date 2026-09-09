<template>
  <div class="max-w-4xl mx-auto py-8 px-4 space-y-6" v-if="policy">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-semibold">{{ policy.policy_number }}</h1>
        <p class="text-sm text-gray-500">{{ policy.status }} · {{ policy.scheme }}</p>
      </div>
      <div class="flex gap-2">
        <Button @click="downloadPrint" :loading="printing">Download Schedule</Button>
        <Button @click="showEndorsement = true">Request Endorsement</Button>
        <Button appearance="primary" @click="$router.push({ path: '/claims/new', query: { policy: policy.name } })">
          Intimate Claim
        </Button>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4 bg-white border rounded-lg p-4">
      <div><div class="text-xs text-gray-500">Sum Assured</div><div class="font-medium">{{ policy.sum_assured }}</div></div>
      <div><div class="text-xs text-gray-500">Total Premium</div><div class="font-medium">{{ policy.total_premium }}</div></div>
      <div><div class="text-xs text-gray-500">Period</div><div class="font-medium">{{ policy.start_date }} – {{ policy.end_date }}</div></div>
      <div><div class="text-xs text-gray-500">Payment</div><div class="font-medium">{{ policy.payment_status }}</div></div>
    </div>

    <section v-if="members.length">
      <h2 class="text-lg font-medium mb-2">Members</h2>
      <div class="bg-white border rounded-lg divide-y">
        <div v-for="m in members" :key="m.name || m.member_name" class="p-3 flex justify-between">
          <span>{{ m.member_name }} <span class="text-gray-500 text-sm">({{ m.relationship }})</span></span>
          <span class="text-sm text-gray-500">Age {{ m.age }}</span>
        </div>
      </div>
    </section>

    <Dialog title="Request Endorsement" v-model="showEndorsement">
      <div class="space-y-3 p-1">
        <label class="block text-sm">Type
          <select v-model="endorsement.type" class="mt-1 w-full border rounded px-2 py-1">
            <option>Address Change</option>
            <option>Nominee Change</option>
            <option>Member Addition</option>
            <option>Member Deletion</option>
            <option>Sum Insured Change</option>
            <option>Correction</option>
          </select>
        </label>
        <label class="block text-sm">New Value
          <input v-model="endorsement.new_value" class="mt-1 w-full border rounded px-2 py-1" />
        </label>
        <label class="block text-sm">Description
          <textarea v-model="endorsement.description" class="mt-1 w-full border rounded px-2 py-1" rows="3" />
        </label>
        <Button appearance="primary" :loading="submitting" @click="submitEndorsement">Submit</Button>
      </div>
    </Dialog>
  </div>
  <div v-else class="p-8 text-gray-500">Loading policy…</div>
</template>

<script>
import { Dialog } from 'frappe-ui'

export default {
  name: 'PolicyDetail',
  components: { Dialog },
  data() {
    return {
      showEndorsement: false,
      submitting: false,
      printing: false,
      endorsement: { type: 'Address Change', new_value: '', description: '' },
    }
  },
  computed: {
    detail() {
      return this.$resources.detail.data
    },
    policy() {
      return this.detail?.policy
    },
    members() {
      return this.detail?.members || []
    },
  },
  resources: {
    detail: {
      url: 'insurance_core.portal.portal_get_policy',
      makeParams() {
        return { policy: this.$route.params.name }
      },
      auto: true,
    },
  },
  methods: {
    async submitEndorsement() {
      this.submitting = true
      try {
        await this.$resources.submitEndorsement.submit({
          policy: this.policy.name,
          endorsement_type: this.endorsement.type,
          description: this.endorsement.description || this.endorsement.type,
          new_value: this.endorsement.new_value,
        })
        this.showEndorsement = false
        this.$toast?.success?.('Endorsement submitted') || alert('Endorsement submitted')
      } finally {
        this.submitting = false
      }
    },
    async downloadPrint() {
      this.printing = true
      try {
        const html = await this.$resources.print.fetch({ policy: this.policy.name })
        const w = window.open('', '_blank')
        if (w) {
          w.document.write(html)
          w.document.close()
        }
      } finally {
        this.printing = false
      }
    },
  },
  resources: {
    detail: {
      url: 'insurance_core.portal.portal_get_policy',
      makeParams() {
        return { policy: this.$route.params.name }
      },
      auto: true,
    },
    submitEndorsement: {
      url: 'insurance_core.portal.portal_request_endorsement',
    },
    print: {
      url: 'insurance_core.portal.portal_policy_print',
    },
  },
}
</script>
