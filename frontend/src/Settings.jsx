import { useState, useRef } from 'react'
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
  const aboutRef = useRef();
  const algoRef = useRef();
  const resourcesRef = useRef();
  const misinfoRef = useRef();

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
          <a onClick={() => aboutRef.current.showModal()} >About Cited</a>
          <a onClick={() => resourcesRef.current.showModal()}>Resources</a>
          <a onClick={() => misinfoRef.current.showModal()}>Misinformation Classification</a>
          <a onClick={() => algoRef.current.showModal()}>How Our Algorithm Works</a>
        </div>
      </footer>

      <dialog ref={aboutRef} className='settings-dialog'>
        <div className="dialog-header">
          <p>About Cited</p>
          <button onClick={() => aboutRef.current.close()}>x</button>
        </div>
        <hr />
        <p>Lorem ipsum dolor sit amet, consectetur adipisicing elit. Consectetur ratione sed eveniet facilis labore. Labore amet adipisci delectus, veniam voluptates officia perferendis voluptate sunt quis asperiores deleniti minima quo inventore.</p>
      </dialog>

      <dialog ref={resourcesRef} className='settings-dialog'>
        <div className="dialog-header">
          <p>Resources</p>
          <button onClick={() => resourcesRef.current.close()}>x</button>
        </div>
        <hr />
        <p>Lorem ipsum dolor sit amet, consectetur adipisicing elit. Consectetur ratione sed eveniet facilis labore. Labore amet adipisci delectus, veniam voluptates officia perferendis voluptate sunt quis asperiores deleniti minima quo inventore.</p>
      </dialog>
      <dialog ref={misinfoRef} className='settings-dialog'>
        <div className="dialog-header">
          <p>Misinformation Classification</p>
          <button onClick={() => misinfoRef.current.close()}>x</button>
        </div>
        <hr />
        <p>Lorem ipsum dolor sit amet, consectetur adipisicing elit. Consectetur ratione sed eveniet facilis labore. Labore amet adipisci delectus, veniam voluptates officia perferendis voluptate sunt quis asperiores deleniti minima quo inventore.</p>
      </dialog>

      <dialog ref={algoRef} className='settings-dialog'>
        <div className="dialog-header">
          <p>How our Algorithm Works</p>
          <button onClick={() => algoRef.current.close()}>x</button>
        </div>
        <hr />
        <p>Lorem ipsum dolor sit amet, consectetur adipisicing elit. Consectetur ratione sed eveniet facilis labore. Labore amet adipisci delectus, veniam voluptates officia perferendis voluptate sunt quis asperiores deleniti minima quo inventore.</p>
      </dialog>

    </div>
  )
}

export default Settings