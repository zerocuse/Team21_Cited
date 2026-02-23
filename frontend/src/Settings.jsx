import { useState } from 'react'
import './Settings.css'

function Toggle({ checked, onChange }) {
  return (
    <label className="toggle">
      <input type="checkbox" checked={checked} onChange={onChange} />
      <span className="slider" />
    </label>
  );
}

function Settings() {
  const [toggle1, setToggle1] = useState(false);
  const [toggle2, setToggle2] = useState(false);

  return (
    <div className="settings-container">

      <h1 className="settings-title">Settings</h1>

      <div className="settings-content">

        <div className="settings-left">
          <div className="settings-option"></div>
          <div className="settings-option"></div>
          <div className="settings-option"></div>
          <div className="settings-option"></div>
          <div className="settings-option"></div>
          <div className="settings-option"></div>
          <div className="settings-option-row">
            <div className="settings-option"></div>
            <div className="settings-suboptions">
              <div className="settings-suboption2"></div>
              <div className="settings-suboption2"></div>
            </div>
          </div>
          <div className="settings-option-row">
            <div className="settings-option"></div>
            <div className="settings-suboption"></div>
          </div>
        </div>

        <div className="settings-right">
          <div className="settings-option-with-toggle">
            <div className="settings-option-admin"></div>
            <Toggle
              checked={toggle1}
              onChange={(e) => setToggle1(e.target.checked)}
            />
          </div>
          <div className="settings-option-with-toggle">
            <div className="settings-option-admin"></div>
            <Toggle
              checked={toggle2}
              onChange={(e) => setToggle2(e.target.checked)}
            />
          </div>
        </div>

      </div>

      <footer>
        <div className="footer-flex">
          <a>About Cited</a><a>Resources</a><a>Misinformation Classification</a><a>How Our Algorithm Works</a>
        </div>
      </footer>

    </div>
  )
}

export default Settings