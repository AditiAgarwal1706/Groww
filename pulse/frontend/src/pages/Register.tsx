import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { Zap } from 'lucide-react'

export function Register() {
  const { register, isLoading } = useAuthStore()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (password.length < 8) { setError('Password must be at least 8 characters'); return }
    try {
      await register(email, password, name)
      navigate('/dashboard')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Registration failed')
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card animate-fadeInUp">
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            width: 48, height: 48, borderRadius: 12,
            background: 'linear-gradient(135deg, #7C3AED, #9D5CF5)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 1rem',
            boxShadow: '0 8px 24px rgba(124,58,237,0.4)',
          }}>
            <Zap size={24} fill="white" color="white" />
          </div>
          <h1 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>Create account</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Start monitoring what matters</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="input-group mb-4">
            <label className="input-label" htmlFor="reg-name">Name</label>
            <input id="reg-name" className="input" type="text" value={name}
              onChange={e => setName(e.target.value)} placeholder="Alex" />
          </div>
          <div className="input-group mb-4">
            <label className="input-label" htmlFor="reg-email">Email</label>
            <input id="reg-email" className="input" type="email" value={email}
              onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required />
          </div>
          <div className="input-group mb-4">
            <label className="input-label" htmlFor="reg-password">Password</label>
            <input id="reg-password" className="input" type="password" value={password}
              onChange={e => setPassword(e.target.value)} placeholder="min 8 characters" required />
          </div>

          {error && (
            <div style={{
              background: 'var(--accent-crimson-dim)', border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 8, padding: '0.625rem 1rem',
              color: 'var(--severity-major)', fontSize: '0.875rem', marginBottom: '1rem',
            }}>
              {error}
            </div>
          )}

          <button id="register-submit-btn" type="submit" className="btn btn-primary w-full btn-lg" disabled={isLoading}
            style={{ justifyContent: 'center' }}>
            {isLoading ? 'Creating...' : 'Create Account'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--accent-violet)', fontWeight: 600 }}>Sign in</Link>
        </p>
      </div>
    </div>
  )
}
