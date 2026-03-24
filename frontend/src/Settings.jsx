import { useState, useRef } from 'react'
import './Settings.css'

const DEFAULTS = {
  factCheckMethod: 'web-scrape',
  resultsPerClaim: 5,
  minWordCount: 3,
  showBreakdown: true,
  showSourceLinks: true,
  saveHistory: true,
  autoScroll: false,
}

function loadSettings() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem('cited_settings') || '{}') }
  } catch {
    return { ...DEFAULTS }
  }
}

function Toggle({ checked, onChange }) {
  return (
    <label className="toggle">
      <input type="checkbox" checked={checked} onChange={onChange} />
      <span className="slider" />
    </label>
  )
}

function Settings() {
  const [settings, setSettings] = useState(loadSettings)
  const aboutRef = useRef()
  const algoRef = useRef()
  const resourcesRef = useRef()
  const misinfoRef = useRef()

  function update(key, value) {
    setSettings(prev => {
      const next = { ...prev, [key]: value }
      localStorage.setItem('cited_settings', JSON.stringify(next))
      return next
    })
  }

  const METHOD_OPTIONS = [
    { id: 'web-scrape',      label: 'Web Scrape',     desc: 'Search the live web for fact-checks' },
    { id: 'cited-database',  label: 'Cited Database', desc: 'Query our curated fact-check database' },
    { id: 'expert-driven',   label: 'Expert-Driven',  desc: 'Route to human expert reviewers' },
  ]

  return (
    <div className="settings-container">

      <h1 className="settings-title">Settings</h1>

      <div className="settings-content">

        {/* ── Left column ── */}
        <div className="settings-left">

          {/* Fact-check Method */}
          <div className="settings-item">
            <div className="settings-item-label">Fact-check Method</div>
            <div className="settings-item-desc">Choose how Cited sources and verifies claims</div>
            <div className="settings-method-group">
              {METHOD_OPTIONS.map(opt => (
                <button
                  key={opt.id}
                  className={`method-btn${settings.factCheckMethod === opt.id ? ' method-btn--active' : ''}`}
                  onClick={() => update('factCheckMethod', opt.id)}
                  title={opt.desc}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <div className="settings-method-desc">
              {METHOD_OPTIONS.find(o => o.id === settings.factCheckMethod)?.desc}
            </div>
          </div>

          {/* Results per claim */}
          <div className="settings-item settings-item-row">
            <div>
              <div className="settings-item-label">Results Per Claim</div>
              <div className="settings-item-desc">Maximum fact-checks displayed per result</div>
            </div>
            <select
              className="settings-select"
              value={settings.resultsPerClaim}
              onChange={e => update('resultsPerClaim', Number(e.target.value))}
            >
              <option value={3}>3</option>
              <option value={5}>5</option>
              <option value={10}>10</option>
            </select>
          </div>

          {/* Minimum word count */}
          <div className="settings-item settings-item-row">
            <div>
              <div className="settings-item-label">Minimum Word Count</div>
              <div className="settings-item-desc">Words required before a query can be submitted</div>
            </div>
            <select
              className="settings-select"
              value={settings.minWordCount}
              onChange={e => update('minWordCount', Number(e.target.value))}
            >
              <option value={1}>1</option>
              <option value={3}>3</option>
              <option value={5}>5</option>
            </select>
          </div>

          {/* Show verdict breakdown */}
          <div className="settings-item settings-item-row">
            <div>
              <div className="settings-item-label">Show Verdict Breakdown</div>
              <div className="settings-item-desc">Display the per-rating tally in search results</div>
            </div>
            <Toggle
              checked={settings.showBreakdown}
              onChange={e => update('showBreakdown', e.target.checked)}
            />
          </div>

          {/* Show source links */}
          <div className="settings-item settings-item-row">
            <div>
              <div className="settings-item-label">Show Source Links</div>
              <div className="settings-item-desc">Display links to the original fact-check articles</div>
            </div>
            <Toggle
              checked={settings.showSourceLinks}
              onChange={e => update('showSourceLinks', e.target.checked)}
            />
          </div>

        </div>

        {/* ── Right column ── */}
        <div className="settings-right">

          <div className="settings-item settings-item-row">
            <div>
              <div className="settings-item-label">Save Search History</div>
              <div className="settings-item-desc">Store queries to your account history</div>
            </div>
            <Toggle
              checked={settings.saveHistory}
              onChange={e => update('saveHistory', e.target.checked)}
            />
          </div>

          <div className="settings-item settings-item-row">
            <div>
              <div className="settings-item-label">Auto-scroll to Results</div>
              <div className="settings-item-desc">Scroll down automatically after submitting a query</div>
            </div>
            <Toggle
              checked={settings.autoScroll}
              onChange={e => update('autoScroll', e.target.checked)}
            />
          </div>

        </div>

      </div>

      <footer>
        <div className="footer-flex">
          <a onClick={() => aboutRef.current.showModal()}>About Cited</a>
          <a onClick={() => resourcesRef.current.showModal()}>Resources</a>
          <a onClick={() => misinfoRef.current.showModal()}>Misinformation Classification</a>
          <a onClick={() => algoRef.current.showModal()}>How Our Algorithm Works</a>
        </div>
      </footer>

      <dialog ref={aboutRef} className='settings-dialog'>
        <div className="dialog-header">
          <p>About Cited</p>
          <button onClick={() => aboutRef.current.close()}>✕</button>
        </div>
        <hr />
        <p>Cited is a fact-checking platform built to help users quickly verify claims using multiple data sources. We combine web scraping, curated databases, and expert-reviewed content to surface the most relevant and trustworthy information available.</p>
      </dialog>

      <dialog ref={resourcesRef} className='settings-dialog'>
        <div className="dialog-header">
          <p>Resources</p>
          <button onClick={() => resourcesRef.current.close()}>✕</button>
        </div>
        <hr />
        <p>Cited draws on trusted sources including Google Fact Check, PolitiFact, Snopes, and FullFact. Our database is continuously updated as new fact-checks are published by accredited organizations worldwide.</p>
      </dialog>

      <dialog ref={misinfoRef} className='settings-dialog'>
        <div className="dialog-header">
          <p>Misinformation Classification</p>
          <button onClick={() => misinfoRef.current.close()}>✕</button>
        </div>
        <hr />
        <p>Claims are classified as <strong>True</strong>, <strong>False</strong>, or <strong>Partially True</strong>. A verdict of <em>Partially True</em> indicates the claim contains accurate elements but is missing important context or includes some inaccuracies.</p>
      </dialog>

      <dialog ref={algoRef} className='settings-dialog'>
        <div className="dialog-header">
          <p>How Our Algorithm Works</p>
          <button onClick={() => algoRef.current.close()}>✕</button>
        </div>
        <hr />
        <p>When you submit a claim, Cited searches for semantically similar fact-checks across its sources. Matches are ranked by similarity and their verdicts are aggregated into an overall verdict. The confidence score reflects how consistent the matched fact-checks are with one another.</p>
      </dialog>

    </div>
  )
}

export default Settings
