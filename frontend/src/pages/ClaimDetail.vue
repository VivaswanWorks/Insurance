<template>
  <div class="max-w-4xl mx-auto py-8 px-4 space-y-6" v-if="claim">
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <button
          class="text-sm text-gray-500 hover:text-gray-800 mb-1"
          @click="$router.push('/claims')">
          ← My Claims
        </button>
        <h1 class="text-2xl font-semibold">{{ claim.claim_number }}</h1>
        <p class="text-sm text-gray-500">
          {{ claim.claim_type }}
          <span v-if="policyNumber"> · {{ policyNumber }}</span>
        </p>
      </div>
      <div class="flex gap-2 flex-wrap items-center">
        <span class="text-xs px-2.5 py-1 rounded-full bg-gray-100 font-medium">{{ claim.status }}</span>
        <Button
          v-if="canDownloadSettlement"
          @click="downloadSettlement"
          :loading="printing">
          Settlement letter
        </Button>
      </div>
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-white border rounded-lg p-4">
      <div>
        <div class="text-xs text-gray-500">Incident date</div>
        <div class="font-medium">{{ formatDate(claim.incident_date) }}</div>
      </div>
      <div>
        <div class="text-xs text-gray-500">Submitted</div>
        <div class="font-medium">{{ formatDate(claim.submission_date) }}</div>
      </div>
      <div>
        <div class="text-xs text-gray-500">Claimed</div>
        <div class="font-medium">{{ formatCurrency(claim.claimed_amount) }}</div>
      </div>
      <div>
        <div class="text-xs text-gray-500">Approved</div>
        <div class="font-medium">{{ formatCurrency(claim.approved_amount) }}</div>
      </div>
      <div v-if="claim.settled_amount">
        <div class="text-xs text-gray-500">Settled</div>
        <div class="font-medium">{{ formatCurrency(claim.settled_amount) }}</div>
      </div>
      <div v-if="claim.claimant">
        <div class="text-xs text-gray-500">Claimant</div>
        <div class="font-medium">{{ claim.claimant }}</div>
      </div>
      <div v-if="claim.hospital">
        <div class="text-xs text-gray-500">Hospital</div>
        <div class="font-medium">{{ claim.hospital }}</div>
      </div>
      <div v-if="claim.admission_date || claim.discharge_date">
        <div class="text-xs text-gray-500">Admission</div>
        <div class="font-medium">
          {{ formatDate(claim.admission_date) }}
          <span v-if="claim.discharge_date"> – {{ formatDate(claim.discharge_date) }}</span>
        </div>
      </div>
    </div>

    <section v-if="claim.description">
      <h2 class="text-lg font-medium mb-2">Description</h2>
      <div class="bg-white border rounded-lg p-4 text-sm text-gray-700 prose prose-sm max-w-none" v-html="claim.description" />
    </section>

    <section v-if="claim.diagnosis || claim.treatment_details">
      <h2 class="text-lg font-medium mb-2">Treatment</h2>
      <div class="bg-white border rounded-lg p-4 space-y-2 text-sm">
        <div v-if="claim.diagnosis">
          <div class="text-xs text-gray-500">Diagnosis</div>
          <div>{{ claim.diagnosis }}</div>
        </div>
        <div v-if="claim.treatment_details" class="prose prose-sm max-w-none" v-html="claim.treatment_details" />
      </div>
    </section>

    <section v-if="claim.rejection_reason">
      <h2 class="text-lg font-medium mb-2 text-red-700">Rejection reason</h2>
      <div class="bg-red-50 border border-red-100 rounded-lg p-4 text-sm text-red-800">
        {{ claim.rejection_reason }}
      </div>
    </section>

    <!-- Documents table + upload -->
    <section>
      <div class="flex items-center justify-between mb-2 flex-wrap gap-2">
        <h2 class="text-lg font-medium">Documents</h2>
        <span class="text-xs text-gray-500">{{ documents.length }} file(s)</span>
      </div>

      <div class="bg-white border rounded-lg overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead class="bg-gray-50 text-left text-xs uppercase text-gray-500">
              <tr>
                <th class="px-4 py-2.5 font-medium">Type</th>
                <th class="px-4 py-2.5 font-medium">File</th>
                <th class="px-4 py-2.5 font-medium">Uploaded</th>
                <th class="px-4 py-2.5 font-medium">Verified</th>
              </tr>
            </thead>
            <tbody class="divide-y">
              <tr v-for="d in documents" :key="d.name || d.attachment">
                <td class="px-4 py-3 font-medium whitespace-nowrap">{{ d.document_type }}</td>
                <td class="px-4 py-3">
                  <a
                    v-if="d.attachment"
                    :href="fileUrl(d.attachment)"
                    target="_blank"
                    rel="noopener"
                    class="text-blue-600 hover:underline">
                    {{ fileName(d.attachment) }}
                  </a>
                  <span v-else class="text-gray-400">—</span>
                </td>
                <td class="px-4 py-3 text-gray-500 whitespace-nowrap">{{ formatDateTime(d.uploaded_on) }}</td>
                <td class="px-4 py-3">
                  <span
                    v-if="d.verified"
                    class="text-xs px-1.5 py-0.5 rounded bg-green-50 text-green-700">
                    Yes
                  </span>
                  <span v-else class="text-xs text-gray-400">No</span>
                </td>
              </tr>
              <tr v-if="!documents.length">
                <td colspan="4" class="px-4 py-6 text-center text-gray-500">
                  No documents uploaded yet.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="canUpload" class="border-t p-4 bg-gray-50 space-y-3">
          <h3 class="text-sm font-medium text-gray-800">Upload document</h3>
          <div class="flex flex-col sm:flex-row gap-3 sm:items-end">
            <label class="block text-sm flex-1">
              Type
              <select v-model="upload.document_type" class="mt-1 w-full border rounded px-2 py-1.5 bg-white">
                <option v-for="t in documentTypes" :key="t" :value="t">{{ t }}</option>
              </select>
            </label>
            <label class="block text-sm flex-1">
              File
              <input
                ref="fileInput"
                type="file"
                class="mt-1 block w-full text-sm"
                accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx"
                @change="onFileChange" />
            </label>
            <Button appearance="primary" :loading="uploading" :disabled="!upload.file" @click="submitUpload">
              Upload
            </Button>
          </div>
          <p v-if="uploadError" class="text-sm text-red-600">{{ uploadError }}</p>
          <p v-if="uploadSuccess" class="text-sm text-green-700">{{ uploadSuccess }}</p>
        </div>
        <div v-else class="border-t px-4 py-3 text-xs text-gray-500 bg-gray-50">
          Document upload is closed for {{ claim.status }} claims.
        </div>
      </div>
    </section>
  </div>
  <div v-else-if="$resources.detail.loading" class="p-8 text-gray-500">Loading claim…</div>
  <div v-else class="p-8 text-red-600 text-sm">{{ $resources.detail.error || 'Claim not found.' }}</div>
</template>

<script>
export default {
  name: 'ClaimDetail',
  data() {
    return {
      printing: false,
      uploading: false,
      uploadError: '',
      uploadSuccess: '',
      upload: {
        document_type: 'Bills',
        file: null,
      },
      documentTypes: [
        'Discharge Summary',
        'Bills',
        'Reports',
        'ID Proof',
        'FIR',
        'Estimate',
        'Other',
      ],
      localDocuments: null,
    }
  },
  computed: {
    detail() {
      return this.$resources.detail.data
    },
    claim() {
      return this.detail?.claim
    },
    policyNumber() {
      return this.detail?.policy_number
    },
    documents() {
      if (this.localDocuments) return this.localDocuments
      return this.detail?.documents || []
    },
    canDownloadSettlement() {
      return ['Settled', 'Approved', 'Partially Approved'].includes(this.claim?.status)
    },
    canUpload() {
      return this.claim && !['Settled', 'Closed', 'Rejected'].includes(this.claim.status)
    },
  },
  watch: {
    '$route.params.name'() {
      this.localDocuments = null
      this.uploadSuccess = ''
      this.uploadError = ''
    },
  },
  resources: {
    detail: {
      url: 'insurance_core.portal.portal_get_claim',
      makeParams() {
        return { claim: this.$route.params.name }
      },
      auto: true,
    },
    print: {
      url: 'insurance_core.portal.portal_claim_print',
    },
    uploadDoc: {
      url: 'insurance_core.portal.portal_upload_claim_document',
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
      if (!value) return '—'
      const d = new Date(value)
      if (Number.isNaN(d.getTime())) return value
      return d.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      })
    },
    formatDateTime(value) {
      if (!value) return '—'
      const d = new Date(value)
      if (Number.isNaN(d.getTime())) return value
      return d.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
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
    onFileChange(e) {
      const files = e.target.files
      this.upload.file = files && files[0] ? files[0] : null
      this.uploadError = ''
      this.uploadSuccess = ''
    },
    async uploadFileToFrappe(file) {
      const formData = new FormData()
      formData.append('file', file, file.name)
      formData.append('is_private', '1')
      formData.append('folder', 'Home/Attachments')
      formData.append('doctype', 'Insurance Claim')
      formData.append('docname', this.claim.name)

      const res = await fetch('/api/method/upload_file', {
        method: 'POST',
        headers: {
          'X-Frappe-CSRF-Token': window.csrf_token || '',
        },
        credentials: 'same-origin',
        body: formData,
      })
      const payload = await res.json()
      if (!res.ok || payload.exc) {
        const msg =
          (payload._server_messages && JSON.parse(payload._server_messages)[0]) ||
          payload.message ||
          payload.exc ||
          'File upload failed'
        throw new Error(typeof msg === 'string' ? msg : 'File upload failed')
      }
      const message = payload.message
      return message?.file_url || message?.file_name || message
    },
    async submitUpload() {
      this.uploadError = ''
      this.uploadSuccess = ''
      if (!this.upload.file) {
        this.uploadError = 'Choose a file to upload.'
        return
      }
      this.uploading = true
      try {
        const file_url = await this.uploadFileToFrappe(this.upload.file)
        const res = await this.$resources.uploadDoc.submit({
          claim: this.claim.name,
          document_type: this.upload.document_type,
          file_url,
        })
        this.localDocuments = res.documents || []
        this.upload.file = null
        if (this.$refs.fileInput) this.$refs.fileInput.value = ''
        this.uploadSuccess = 'Document uploaded successfully.'
        // refresh full claim payload in background
        this.$resources.detail.reload()
      } catch (e) {
        this.uploadError = e.message || 'Upload failed'
      } finally {
        this.uploading = false
      }
    },
    async downloadSettlement() {
      this.printing = true
      try {
        const html = await this.$resources.print.fetch({
          claim: this.claim.name,
          settlement: 1,
        })
        const w = window.open('', '_blank')
        if (w) {
          w.document.write(html)
          w.document.close()
        }
      } catch (e) {
        alert(e.message || 'Could not load settlement letter')
      } finally {
        this.printing = false
      }
    },
  },
}
</script>
