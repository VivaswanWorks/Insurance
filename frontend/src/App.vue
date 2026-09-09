<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 flex">
    <!-- Mobile overlay -->
    <div
      v-if="mobileOpen"
      class="fixed inset-0 bg-black/40 z-30 lg:hidden"
      @click="mobileOpen = false" />

    <!-- Sidebar -->
    <aside
      class="fixed lg:sticky top-0 left-0 z-40 h-screen flex flex-col bg-white border-r border-gray-200 transition-all duration-200"
      :class="[
        collapsed ? 'w-[4.25rem]' : 'w-60',
        mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
      ]">
      <div class="h-14 flex items-center gap-2 px-3 border-b shrink-0">
        <button
          class="hidden lg:inline-flex h-9 w-9 items-center justify-center rounded-md text-gray-600 hover:bg-gray-100"
          :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          @click="collapsed = !collapsed">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <router-link
          to="/"
          class="font-semibold tracking-tight text-gray-900 no-underline truncate"
          :class="collapsed ? 'sr-only lg:hidden' : ''"
          @click="mobileOpen = false">
          Insurance Portal
        </router-link>
      </div>

      <nav class="flex-1 overflow-y-auto py-3 px-2 space-y-4">
        <div v-for="group in navGroups" :key="group.title">
          <div
            v-if="!collapsed"
            class="px-2 mb-1 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
            {{ group.title }}
          </div>
          <div class="space-y-0.5">
            <router-link
              v-for="item in group.items"
              :key="item.to"
              :to="item.to"
              class="flex items-center gap-3 rounded-md px-2.5 py-2 text-sm text-gray-600 no-underline hover:bg-gray-100 hover:text-gray-900"
              :class="isActive(item) ? 'bg-gray-100 text-gray-900 font-medium' : ''"
              :title="item.label"
              @click="mobileOpen = false">
              <span class="shrink-0 w-5 h-5 flex items-center justify-center text-gray-500" v-html="item.icon" />
              <span v-show="!collapsed" class="truncate">{{ item.label }}</span>
            </router-link>
          </div>
        </div>
      </nav>

      <div class="border-t p-2 shrink-0">
        <button
          class="w-full flex items-center gap-3 rounded-md px-2.5 py-2 text-sm text-gray-600 hover:bg-gray-100"
          :title="collapsed ? 'Expand' : 'Collapse'"
          @click="collapsed = !collapsed">
          <span class="shrink-0 w-5 h-5 flex items-center justify-center">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                :d="collapsed ? 'M9 5l7 7-7 7' : 'M15 19l-7-7 7-7'" />
            </svg>
          </span>
          <span v-show="!collapsed">Collapse</span>
        </button>
      </div>
    </aside>

    <!-- Main column -->
    <div class="flex-1 min-w-0 flex flex-col min-h-screen">
      <!-- Top bar: search + profile -->
      <header class="sticky top-0 z-20 bg-white border-b h-14 flex items-center gap-3 px-3 sm:px-4">
        <button
          class="lg:hidden h-9 w-9 inline-flex items-center justify-center rounded-md text-gray-600 hover:bg-gray-100"
          @click="mobileOpen = true">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <div class="relative flex-1 max-w-xl" data-search-root>
          <div class="pointer-events-none absolute inset-y-0 left-0 pl-3 flex items-center text-gray-400">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 21l-4.35-4.35M11 18a7 7 0 100-14 7 7 0 000 14z" />
            </svg>
          </div>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Search policies, claims…"
            class="w-full h-9 pl-9 pr-3 rounded-md border border-gray-200 bg-gray-50 text-sm focus:outline-none focus:ring-2 focus:ring-gray-300 focus:bg-white"
            @focus="searchOpen = true"
            @keydown.escape="closeSearch"
            @keydown.enter.prevent="goFirstResult" />

          <div
            v-if="searchOpen && searchQuery.trim().length >= 2"
            class="absolute left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg overflow-hidden z-30">
            <div v-if="$resources.search.loading" class="px-3 py-3 text-sm text-gray-500">Searching…</div>
            <template v-else>
              <div v-if="searchResults.policies.length" class="py-1">
                <div class="px-3 py-1 text-[11px] font-semibold uppercase text-gray-400">Policies</div>
                <button
                  v-for="p in searchResults.policies"
                  :key="p.name"
                  class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex justify-between gap-2"
                  @click="goTo(`/policies/${p.name}`)">
                  <span class="truncate">
                    <span class="font-medium">{{ p.policy_number }}</span>
                    <span class="text-gray-500"> · {{ p.scheme }}</span>
                  </span>
                  <span class="text-xs text-gray-400 shrink-0">{{ p.status }}</span>
                </button>
              </div>
              <div v-if="searchResults.claims.length" class="py-1 border-t">
                <div class="px-3 py-1 text-[11px] font-semibold uppercase text-gray-400">Claims</div>
                <button
                  v-for="c in searchResults.claims"
                  :key="c.name"
                  class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex justify-between gap-2"
                  @click="goTo(`/claims/${c.name}`)">
                  <span class="truncate">
                    <span class="font-medium">{{ c.claim_number }}</span>
                    <span class="text-gray-500"> · {{ c.claim_type }}</span>
                  </span>
                  <span class="text-xs text-gray-400 shrink-0">{{ c.status }}</span>
                </button>
              </div>
              <div
                v-if="!searchResults.policies.length && !searchResults.claims.length"
                class="px-3 py-3 text-sm text-gray-500">
                No matches for “{{ searchQuery }}”
              </div>
            </template>
          </div>
        </div>

        <!-- Profile dropdown -->
        <div class="relative shrink-0" ref="profileRoot">
          <button
            class="flex items-center gap-2 rounded-md pl-1 pr-2 py-1 hover:bg-gray-100"
            @click="profileOpen = !profileOpen">
            <span
              class="h-8 w-8 rounded-full bg-gray-800 text-white text-xs font-semibold flex items-center justify-center overflow-hidden">
              <img v-if="userImage" :src="userImage" alt="" class="h-full w-full object-cover" />
              <span v-else>{{ userInitials }}</span>
            </span>
            <span class="hidden sm:block text-sm font-medium max-w-[9rem] truncate">{{ displayName }}</span>
            <svg class="w-4 h-4 text-gray-500 hidden sm:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div
            v-if="profileOpen"
            class="absolute right-0 mt-1 w-56 bg-white border rounded-lg shadow-lg py-1 z-30">
            <div class="px-3 py-2 border-b">
              <div class="text-sm font-medium truncate">{{ displayName }}</div>
              <div class="text-xs text-gray-500 truncate">{{ userEmail }}</div>
            </div>
            <router-link
              to="/"
              class="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 no-underline"
              @click="profileOpen = false">
              Dashboard
            </router-link>
            <router-link
              to="/policies"
              class="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 no-underline"
              @click="profileOpen = false">
              My policies
            </router-link>
            <router-link
              to="/claims"
              class="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 no-underline"
              @click="profileOpen = false">
              My claims
            </router-link>
            <a
              href="/app/user-profile"
              class="block px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 no-underline"
              @click="profileOpen = false">
              Account settings
            </a>
            <div class="border-t my-1" />
            <button
              class="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50"
              :disabled="loggingOut"
              @click="logout">
              {{ loggingOut ? 'Signing out…' : 'Log out' }}
            </button>
          </div>
        </div>
      </header>

      <main class="flex-1">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script>
const icon = {
  home: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M3 12l9-9 9 9M5 10v10h5v-6h4v6h5V10"/></svg>`,
  policy: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M9 12h6m-6 4h6M7 4h10a2 2 0 012 2v14l-3-2-3 2-3-2-3 2V6a2 2 0 012-2z"/></svg>`,
  claim: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>`,
  plus: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M12 4v16m8-8H4"/></svg>`,
}

export default {
  name: 'App',
  data() {
    return {
      collapsed: false,
      mobileOpen: false,
      profileOpen: false,
      searchOpen: false,
      searchQuery: '',
      searchTimer: null,
      loggingOut: false,
      navGroups: [
        {
          title: 'Overview',
          items: [{ to: '/', label: 'Dashboard', icon: icon.home, exact: true }],
        },
        {
          title: 'Policies',
          items: [{ to: '/policies', label: 'My Policies', icon: icon.policy, match: '/policies' }],
        },
        {
          title: 'Claims',
          items: [
            { to: '/claims', label: 'My Claims', icon: icon.claim, match: '/claims', exclude: '/claims/new' },
            { to: '/claims/new', label: 'Intimate Claim', icon: icon.plus, exact: true },
          ],
        },
      ],
    }
  },
  computed: {
    me() {
      return this.$resources.me?.data
    },
    displayName() {
      return this.me?.client?.full_name || this.me?.user?.full_name || 'Account'
    },
    userEmail() {
      return this.me?.client?.email || this.me?.user?.email || ''
    },
    userImage() {
      const img = this.me?.user?.user_image
      if (!img) return ''
      return img.startsWith('/') || /^https?:/i.test(img) ? img : `/${img}`
    },
    userInitials() {
      const name = this.displayName || '?'
      const parts = name.trim().split(/\s+/).filter(Boolean)
      if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
      return name.slice(0, 2).toUpperCase()
    },
    searchResults() {
      return this.$resources.search?.data || { policies: [], claims: [] }
    },
  },
  resources: {
    me: {
      url: 'insurance_core.portal.portal_me',
      auto: true,
    },
    search: {
      url: 'insurance_core.portal.portal_search',
    },
  },
  watch: {
    searchQuery(q) {
      clearTimeout(this.searchTimer)
      if (!q || q.trim().length < 2) {
        return
      }
      this.searchTimer = setTimeout(() => {
        this.$resources.search.fetch({ q: q.trim(), limit: 8 })
        this.searchOpen = true
      }, 250)
    },
    $route() {
      this.mobileOpen = false
      this.closeSearch()
      this.profileOpen = false
    },
    collapsed(v) {
      localStorage.setItem('insurance_portal_sidebar_collapsed', v ? '1' : '0')
    },
  },
  mounted() {
    document.addEventListener('click', this.onDocClick)
    const saved = localStorage.getItem('insurance_portal_sidebar_collapsed')
    if (saved === '1') this.collapsed = true
  },
  beforeUnmount() {
    document.removeEventListener('click', this.onDocClick)
    clearTimeout(this.searchTimer)
  },
  methods: {
    isActive(item) {
      const path = this.$route.path
      if (item.exact) return path === item.to
      if (item.match) {
        if (!path.startsWith(item.match)) return false
        if (item.exclude && path.startsWith(item.exclude)) return false
        if (item.to === '/claims' && path === '/claims/new') return false
        return true
      }
      return path === item.to || path.startsWith(item.to + '/')
    },
    closeSearch() {
      this.searchOpen = false
    },
    goTo(path) {
      this.closeSearch()
      this.searchQuery = ''
      this.$router.push(path)
    },
    goFirstResult() {
      const r = this.searchResults
      if (r.policies?.length) return this.goTo(`/policies/${r.policies[0].name}`)
      if (r.claims?.length) return this.goTo(`/claims/${r.claims[0].name}`)
    },
    onDocClick(e) {
      if (this.$refs.profileRoot && !this.$refs.profileRoot.contains(e.target)) {
        this.profileOpen = false
      }
      if (this.searchOpen && !e.target.closest?.('[data-search-root]')) {
        this.searchOpen = false
      }
    },
    async logout() {
      this.loggingOut = true
      try {
        await fetch('/api/method/logout', {
          method: 'POST',
          headers: {
            'X-Frappe-CSRF-Token': window.csrf_token || '',
            'Content-Type': 'application/json',
          },
          credentials: 'same-origin',
          body: '{}',
        })
      } catch (e) {
        // still redirect
      } finally {
        window.location.href = '/login?redirect-to=/insurance_core'
      }
    },
  },
}
</script>
