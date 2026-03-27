import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../services/api'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const form = new URLSearchParams()
        form.append('username', email)
        form.append('password', password)
        const { data } = await api.post('/api/auth/login', form, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        })
        set({ user: data.user, token: data.access_token, isAuthenticated: true })
        api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
        return data
      },

      register: async (email, username, password) => {
        const { data } = await api.post('/api/auth/register', { email, username, password })
        set({ user: data.user, token: data.access_token, isAuthenticated: true })
        api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
        return data
      },

      logout: () => {
        set({ user: null, token: null, isAuthenticated: false })
        delete api.defaults.headers.common['Authorization']
      },

      initAuth: () => {
        const { token } = get()
        if (token) {
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`
        }
      },
    }),
    { name: 'dataai-auth', partialize: (s) => ({ user: s.user, token: s.token, isAuthenticated: s.isAuthenticated }) }
  )
)
