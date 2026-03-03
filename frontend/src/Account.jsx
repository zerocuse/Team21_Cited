import { useState, useRef } from 'react'

import './Account.css'

function Account() {
	const loginRef = useRef();
	const [isLoggedIn, setIsLoggedIn] = useState(false);
	const [user, setUser] = useState(false);

	function handleLogin(e) {
		e.preventDefault();
		setIsLoggedIn(true);
		loginRef.current.close();
	}

  return (
    <>
    <div className="account-page-container">

		<div className="account-header-container">
			<h1 className="account-header">Account</h1>
			{!isLoggedIn && (<button className='login-button' onClick={() => loginRef.current.showModal()}>Log In</button>)}
		</div>

		<dialog className="login-dialog" ref={loginRef}>
			<div className="login-dialog-header">
				<h3>Login or Create Account</h3>
				<p onClick={() => loginRef.current.close()}>x</p>
			</div>
			<form onSubmit={handleLogin}>
				<input type="text" placeholder="Email" required />
				<input type="password" placeholder="Password" required />
				<div className="login-dialog-buttons">
					<button type="button">Create Account</button>
					<button type="submit">Log In</button>
				</div>
			</form>
		</dialog>

        <div className="account-details-container">
			<div className="profile-photo">
				icon
			</div>
			<div className="account-details">
				<div className="account-name">
					<div className="first-name-field">firstname</div>
					<div className="last-name-field">lastname</div>
				</div>
				<div className="username-field">
					username/email
				</div>
				<div className="subscribe-field">
					subscribe pls
				</div>
			</div>
			<div className="membership-status">
				<img src="/src/assets/membership-star_icon.svg" alt="member" className="member-icon" />
			</div>
        </div>

		<h3 className="history-header">History</h3>

		<div className="history-container">
			<div className="history-placeholder">prev1</div>
			<div className="history-placeholder">prev2</div>
			<div className="history-placeholder">prev3</div>
			<div className="history-placeholder">prev4</div>
			<div className="history-placeholder">prev5</div>
		</div>

    </div>
    </>
  )
}

export default Account