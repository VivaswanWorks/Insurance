<template>
  <div class="max-w-4xl mx-auto py-8 px-4 space-y-6" v-if="policy">
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-2xl font-semibold">{{ policy.policy_number }}</h1>
        <p class="text-sm text-gray-500">{{ policy.status }} · {{ policy.scheme }}</p>
      </div>
      <div class="flex gap-2 flex-wrap">
        <Button @click="downloadPrint" :loading="printing">Download Schedule</Button>
        <Button @click="showEndorsement = true">Request Endorsement</Button>
        <Button appearance="primary" @click="$router.push({ path: '/claims/new', query: { policy: policy.name } })">
          Intimate Claim
        </Button>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-4 bg-white border rounded-lg p-4">
      <div><div class="text-xs text-gray-500">Sum Assured</div><div class="font-medium">{{ formatCurrency(policy.sum_assured) }}</div></div>
      <div><div class="text-xs text-gray-500">Total Premium</div><div class="font-medium">{{ formatCurrency(policy.total_premium) }}</div></div>
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

    <section v-if="coverages.length">
      <h2 class="text-lg font-medium mb-2">Coverages</h2>
      <div class="bg-white border rounded-lg divide-y">
        <div
          v-for="c in coverages"
          :key="c.name || c.coverage_name"
          class="p-3 flex flex-wrap gap-2 justify-between items-start">
          <div class="min-w-0 flex-1">
            <div class="font-medium flex items-center gap-2 flex-wrap">
              <span>{{ c.coverage_name }}</span>
              <span
                v-if="c.is_mandatory"
                class="text-xs px-1.5 py-0.5 rounded bg-blue-50 text-blue-700">
                Mandatory
              </span>
            </div>
            <p v-if="c.description" class="text-sm text-gray-500 mt-0.5">{{ c.description }}</p>
            <p v-if="c.notes" class="text-xs text-gray-400 mt-1">{{ c.notes }}</p>
          </div>
          <div class="text-right text-sm shrink-0">
            <div v-if="c.max_limit != null && c.max_limit !== ''" class="font-medium">
              {{ formatCurrency(c.max_limit) }}
            </div>
            <div v-if="c.percentage != null && c.percentage !== ''" class="text-gray-500">
              {{ c.percentage }}% of SI
            </div>
          </div>
        </div>
      </div>
    </section>

    <section v-if="hasDocuments">
      <h2 class="text-lg font-medium mb-2">Documents</h2>
      <div class="bg-white border rounded-lg divide-y">
        <a
          v-if="policy.policy_document"
          :href="fileUrl(policy.policy_document)"
          target="_blank"
          rel="noopener"
          class="p-3 flex justify-between items-center hover:bg-gray-50 no-underline text-inherit">
          <div>
            <div class="font-medium">Policy Document</div>
            <div class="text-sm text-gray-500">PDF schedule / policy copy</div>
          </div>
          <span class="text-sm text-blue-600">Open</span>
        </a>
        <a
          v-if="policy.proposal_form"
          :href="fileUrl(policy.proposal_form)"
          target="_blank"
          rel="noopener"
          class="p-3 flex justify-between items-center hover:bg-gray-50 no-underline text-inherit">
          <div>
            <div class="font-medium">Proposal Form</div>
            <div class="text-sm text-gray-500">Submitted proposal</div>
          </div>
          <span class="text-sm text-blue-600">Open</span>
        </a>
        <a
          v-for="d in documents"
          :key="d.name || d.attachment || d.document_type"
          :href="d.attachment ? fileUrl(d.attachment) : undefined"
          :target="d.attachment ? '_blank' : undefined"
          :rel="d.attachment ? 'noopener' : undefined"
          class="p-3 flex justify-between items-center hover:bg-gray-50 no-underline text-inherit"
          :class="{ 'pointer-events-none opacity-60': !d.attachment }">
          <div>
            <div class="font-medium">{{ d.document_type || 'Document' }}</div>
            <div class="text-sm text-gray-500">
              <span v-if="d.uploaded_on">Uploaded {{ formatDate(d.uploaded_on) }}</span>
              <span v-else-if="d.attachment">{{ fileName(d.attachment) }}</span>
              <span v-else>No file attached</span>
            </div>
          </div>
          <span v-if="d.attachment" class="text-sm text-blue-600">Open</span>
        </a>
        <div
          v-if="!policy.policy_document && !policy.proposal_form && !documents.length"
          class="p-4 text-sm text-gray-500">
          No documents available.
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
    coverages() {
      return this.detail?.coverages || []
    },
    documents() {
      return this.detail?.documents || []
    },
    hasDocuments() {
      return !!(this.policy?.policy_document || this.policy?.proposal_form || this.documents.length)
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
  methods: {
    formatCurrency(value) {
      if (value == null || value === '') return '—'
      const n = Number(value)
      if (Number.isNaN(n)) return value
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0,
      }).format(n)
    },
    formatDate(value) {
      if (!value) return ''
      const d = new Date(value)
      if (Number.isNaN(d.getTime())) return value
      return d.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      })
    },
    fileUrl(path) {
      if (!path) return '#'
      if (/^https?:\/\//i.test(path)) return path
      return path.startsWith('/') ? path : `/files/${path.replace(/^\/?files\//, '')}`
    },
    fileName(path) {
      if (!path) return ''
      const parts = String(path).split('/')
      return parts[parts.length - 1] || path
    },
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
        alert('Endorsement submitted')
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
}
</script>
