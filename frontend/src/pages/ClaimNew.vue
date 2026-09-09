<template>
  <div class="max-w-xl mx-auto py-8 px-4 space-y-6">
    <h1 class="text-2xl font-semibold">Intimate a Claim</h1>

    <div class="bg-white border rounded-lg p-4 space-y-4">
      <label class="block text-sm">Policy
        <select v-model="form.policy" class="mt-1 w-full border rounded px-2 py-1">
          <option disabled value="">Select policy</option>
          <option v-for="p in policies" :key="p.name" :value="p.name">
            {{ p.policy_number }} ({{ p.status }})
          </option>
        </select>
      </label>
      <label class="block text-sm">Claim Type
        <select v-model="form.claim_type" class="mt-1 w-full border rounded px-2 py-1">
          <option>Reimbursement</option>
          <option>Cashless</option>
          <option>Hospitalization</option>
          <option>Accident</option>
          <option>Other</option>
        </select>
      </label>
      <label class="block text-sm">Incident Date
        <input type="date" v-model="form.incident_date" class="mt-1 w-full border rounded px-2 py-1" />
      </label>
      <label class="block text-sm">Claimed Amount
        <input type="number" v-model="form.claimed_amount" class="mt-1 w-full border rounded px-2 py-1" />
      </label>
      <label class="block text-sm">Claimant Name
        <input v-model="form.claimant" class="mt-1 w-full border rounded px-2 py-1" />
      </label>
      <label class="block text-sm">Description
        <textarea v-model="form.description" rows="4" class="mt-1 w-full border rounded px-2 py-1" />
      </label>
      <div class="flex gap-2">
        <Button appearance="primary" :loading="submitting" @click="submit">Submit Claim</Button>
        <Button @click="$router.push('/claims')">Cancel</Button>
      </div>
      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      <p v-if="success" class="text-sm text-green-700">Claim submitted: {{ success }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ClaimNew',
  data() {
    return {
      form: {
        policy: this.$route.query.policy || '',
        claim_type: 'Reimbursement',
        incident_date: '',
        claimed_amount: '',
        claimant: '',
        description: '',
      },
      submitting: false,
      error: '',
      success: '',
    }
  },
  computed: {
    policies() {
      return this.$resources.policies.data || []
    },
  },
  resources: {
    policies: {
      url: 'insurance_core.portal.portal_list_policies',
      auto: true,
    },
    intimate: {
      url: 'insurance_core.portal.portal_intimate_claim',
    },
  },
  methods: {
    async submit() {
      this.error = ''
      this.success = ''
      if (!this.form.policy || !this.form.claimed_amount) {
        this.error = 'Policy and claimed amount are required.'
        return
      }
      this.submitting = true
      try {
        const res = await this.$resources.intimate.submit({ ...this.form })
        this.success = res.claim_number || res.name
        setTimeout(() => this.$router.push('/claims'), 800)
      } catch (e) {
        this.error = e.message || 'Failed to submit claim'
      } finally {
        this.submitting = false
      }
    },
  },
}
</script>
