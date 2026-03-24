import { useState, useRef, useEffect } from 'react'
import './Account.css'

const API = 'http://127.0.0.1:5001/auth'

const BADGE_LABEL = { free: 'Free', premium: 'Premium', admin: 'Admin' }

function Account() {
  const loginRef     = useRef()
  const fileInputRef = useRef()
  const [isLogin, setIsLogin]         = useState(true)
  const [user, setUser]               = useState(null)
  const [error, setError]             = useState('')
  const [loading, setLoading]         = useState(false)
  const [avatarError, setAvatarError] = useState(false)
  const [authReady, setAuthReady]     = useState(false)
  const [history, setHistory]         = useState([])

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) { setAuthReady(true); return }
    fetch(API + '/me', { headers: { 'Authorization': `Bearer ${token}` } })
      .then(res => res.ok ? res.json() : Promise.reject())
      .then(data => {
        setUser(data)
        fetch(API + '/history', { headers: { 'Authorization': `Bearer ${token}` } })
          .then(res => res.ok ? res.json() : [])
          .then(data => setHistory(data))
          .catch(() => {})
      })
      .catch(() => localStorage.removeItem('token'))
      .finally(() => setAuthReady(true))
  }, [])

  const [form, setForm] = useState({
    email: '', password: '', first_name: '', last_name: '', username: ''
  })

  function handleChange(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)

    const endpoint = isLogin ? '/login' : '/register'
    const body = isLogin
      ? { email_address: form.email, password: form.password }
      : {
          email_address: form.email,
          password:      form.password,
          first_name:    form.first_name,
          last_name:     form.last_name,
          username:      form.username,
        }

    try {
      const res = await fetch(API + endpoint, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(body),
      })

      let data = {}
      try { data = await res.json() } catch { /* non-JSON response */ }

      if (!res.ok) {
        setError(data.error || `Server error (${res.status}) — check backend terminal`)
      } else {
        localStorage.setItem('token', data.token)
        setUser(data.user)
        loginRef.current.close()
      }
    } catch {
      setError('Could not reach server — is the backend running on port 5001?')
    } finally {
      setLoading(false)
    }
  }

  async function handleAvatarUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    const token = localStorage.getItem('token')
    try {
      const res = await fetch(API + '/upload-avatar', {
        method:  'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body:    formData,
      })
      const data = await res.json()
      if (res.ok) {
        setAvatarError(false)
        setUser(u => ({ ...u, profile_picture: data.profile_picture }))
      } else {
        setError(data.error || 'Upload failed')
      }
    } catch (err) {
      setError('Could not reach server')
      console.error('Avatar upload error:', err)
    }
    e.target.value = ''
  }

  function handleLogout() {
    localStorage.removeItem('token')
    setUser(null)
  }

  function openModal(asLogin) {
    setIsLogin(asLogin)
    setError('')
    setForm({ email: '', password: '', first_name: '', last_name: '', username: '' })
    loginRef.current.showModal()
  }

  return (
    <div className="account-page-container">

      {/* ── Auth dialog ── */}
      <dialog className="login-dialog" ref={loginRef}>
        <div className="login-dialog-header">
          <h3>{isLogin ? 'Log In' : 'Create Account'}</h3>
          <p onClick={() => loginRef.current.close()}>✕</p>
        </div>
        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <>
              <input name="first_name" type="text"     placeholder="First name" value={form.first_name} onChange={handleChange} required />
              <input name="last_name"  type="text"     placeholder="Last name"  value={form.last_name}  onChange={handleChange} required />
              <input name="username"   type="text"     placeholder="Username"   value={form.username}   onChange={handleChange} required />
            </>
          )}
          <input name="email"    type="email"    placeholder="Email"    value={form.email}    onChange={handleChange} required />
          <input name="password" type="password" placeholder="Password" value={form.password} onChange={handleChange} required />
          {error && <p className="auth-error">{error}</p>}
          <div className="login-dialog-buttons">
            <button type="button" onClick={() => setIsLogin(v => !v)}>
              {isLogin ? 'Create Account' : 'Already have an account?'}
            </button>
            <button type="submit" disabled={loading}>
              {loading ? '…' : isLogin ? 'Log In' : 'Register'}
            </button>
          </div>
        </form>
      </dialog>

      {/* ── Guest screen ── */}
      {authReady && !user && (
        <div className="guest-screen">
          <div className="guest-card">
            <img src="/src/assets/account_icon.svg" alt="Account" className="guest-icon" />
            <h2 className="guest-title">Welcome to Cited.</h2>
            <p className="guest-subtitle">
              Sign in to track your fact-checking history and manage your account.
            </p>
            <div className="guest-buttons">
              <button className="btn-primary" onClick={() => openModal(true)}>Log In</button>
              <button className="btn-secondary" onClick={() => openModal(false)}>Create Account</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Logged-in screen ── */}
      {user && (
        <div className="account-user-content">
          <div className="account-header-container">
            <h1 className="account-header">Account</h1>
            <button className="login-button" onClick={handleLogout}>Log Out</button>
          </div>

          <div className="profile-card">
            {/* Avatar */}
            <div
              className="profile-photo profile-photo--clickable"
              onClick={() => fileInputRef.current.click()}
            >
              {user.profile_picture && !avatarError
                ? <img src={user.profile_picture} alt="Profile" className="profile-pic-img" onError={() => setAvatarError(true)} />
                : <img src="/src/assets/account_icon.svg" alt="Placeholder" className="profile-pic-placeholder" />
              }
              <div className="profile-photo-overlay">Upload</div>
              <input
                type="file"
                ref={fileInputRef}
                style={{ display: 'none' }}
                accept="image/png, image/jpeg, image/gif, image/webp"
                onChange={handleAvatarUpload}
              />
            </div>

            {/* Info */}
            <div className="profile-info">
              <div className="name-and-member">
              <span className="profile-fullname">{user.first_name} {user.last_name}</span>
              <span className={`membership-badge membership-badge--${user.membership_status}`}>
                {BADGE_LABEL[user.membership_status] ?? user.membership_status}
              </span>
              </div>
              <span className="profile-username">@{user.username}</span>

              <hr className="profile-divider" />
              <div className="profile-fields">
                <div className="profile-field">
                  <span className="field-label">Email</span>
                  <span className="field-value">{user.email}</span>
                </div>
                {user.creation_date && (
                  <div className="profile-field">
                    <span className="field-label">Member since</span>
                    <span className="field-value">{user.creation_date}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="history-section">
            <h3 className="history-header">History</h3>
            <div className="history-container">
              {history.length === 0
                ? <p style={{ color: '#aaa', fontSize: '0.9rem' }}>No queries yet.</p>
                : history.map(item => (
                  <div key={item.id} className="history-placeholder">
                    <p style={{ fontWeight: 600, color: '#333', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                      {item.claim_text.length > 100 ? item.claim_text.slice(0, 100) + '…' : item.claim_text}
                    </p>
                    {item.status && (
                      <span style={{
                        fontSize: '0.75rem',
                        padding: '2px 8px',
                        borderRadius: '12px',
                        background: item.status === 'true' ? '#d4edda' : item.status === 'false' ? '#f8d7da' : '#fff3cd',
                        color: item.status === 'true' ? '#155724' : item.status === 'false' ? '#721c24' : '#856404',
                      }}>
                        {item.status}
                      </span>
                    )}
                    {item.queried_at && (
                      <p style={{ color: '#aaa', fontSize: '0.75rem', marginTop: '0.5rem' }}>{item.queried_at}</p>
                    )}
                  </div>
                ))
              }
            </div>
          </div>
        </div>
      )}

    </div>
  )
}

export default Account
