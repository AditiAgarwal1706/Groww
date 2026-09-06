import { useNavigate, NavLink } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { LayoutDashboard, ListChecks, LogOut, Zap } from 'lucide-react'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/watchlist',  icon: ListChecks,      label: 'Watchlist' },
]

export function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-mark">
          <Zap size={16} fill="white" />
        </div>
        <span className="sidebar-logo-text">PULSE</span>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <Icon className="nav-icon" size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div style={{ padding: '0.5rem', marginBottom: '0.5rem' }}>
          <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
            {user?.name || user?.email?.split('@')[0] || 'User'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {user?.email}
          </div>
        </div>
        <button className="nav-item btn-ghost" onClick={handleLogout} style={{ width: '100%', color: 'var(--text-secondary)' }}>
          <LogOut size={16} />
          Sign out
        </button>
      </div>
    </aside>
  )
}
