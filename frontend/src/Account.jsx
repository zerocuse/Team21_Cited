import { useState } from 'react'

import './Account.css'

function Account() {

  return (
    <>
    <div className="account-page-container">

        <h1 className="account-header">Account</h1>

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