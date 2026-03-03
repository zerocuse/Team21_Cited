import { useState, useRef } from 'react'
import './Account.css'

const API = 'http://localhost:5173/auth'

function Account() {
  const loginRef  = useRef()
  const [isLogin, setIsLogin]     = useState(true)
  const [user, setUser]           = useState(null)
  const [error, setError]         = useState('')
  const [loading, setLoading]     = useState(false)

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
    const body     = isLogin
      ? { email_address: form.email, password: form.password }
      : {
          email_address: form.email,
          password:      form.password,
          first_name:    form.first_name,
          last_name:     form.last_name,
          username:      form.username,
        }

    try {
      const res  = await fetch(API + endpoint, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(body),
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.error || 'Something went wrong')
      } else {
        localStorage.setItem('token', data.token)
        setUser(data.user)
        loginRef.current.close()
      }
    } catch {
      setError('Could not reach server')
    } finally {
      setLoading(false)
    }
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
    <>
    <div className="account-page-container">

      <div className="account-header-container">
        <h1 className="account-header">Account</h1>
        {!user && (
          <div>
            <button className='login-button' onClick={() => openModal(true)}>Log In</button>
          </div>
        )}
        {user && <button className='login-button' onClick={handleLogout}>Log Out</button>}
      </div>

      {/* ── Auth dialog ── */}
      <dialog className="login-dialog" ref={loginRef}>
        <div className="login-dialog-header">
          <h3>{isLogin ? 'Log In' : 'Create Account'}</h3>
          <p style={{ cursor: 'pointer' }} onClick={() => loginRef.current.close()}>✕</p>
        </div>

        <form onSubmit={handleSubmit}>
          {!isLogin && (
            <>
              <input name="first_name" type="text" placeholder="First name"
                value={form.first_name} onChange={handleChange} required />
              <input name="last_name"  type="text" placeholder="Last name"
                value={form.last_name}  onChange={handleChange} required />
              <input name="username"   type="text" placeholder="Username"
                value={form.username}   onChange={handleChange} required />
            </>
          )}
          <input name="email"    type="email"    placeholder="Email"
            value={form.email}    onChange={handleChange} required />
          <input name="password" type="password" placeholder="Password"
            value={form.password} onChange={handleChange} required />

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

      {/* ── Profile section ── */}
      <div className="account-details-container">
        <div className="profile-photo">icon</div>
        <div className="account-details">
          <div className="account-name">
            <div className="first-name-field">{user?.first_name || 'First'}</div>
            <div className="last-name-field">{user?.last_name  || 'Last'}</div>
          </div>
          <div className="username-field">{user?.username || 'username/email'}</div>
          <div className="subscribe-field">{user?.is_member ? '⭐ Member' : 'Subscribe'}</div>
        </div>
        <div className="membership-status">
          <img src="/src/assets/membership-star_icon.svg" alt="member" className="member-icon" />
        </div>
      </div>

      <h3 className="history-header">History</h3>
      <div className="history-container">
        {['prev1','prev2','prev3','prev4','prev5'].map(p => (
          <div key={p} className="history-placeholder">{p}</div>
        ))}
      </div>

    </div>
    </>
  )
}

export default Account