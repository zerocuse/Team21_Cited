import './App.css'

import Search from "./search/search"

function App() {
  return (
    <> 
      <div className="stage">
        <nav className="navbar-card" id="navbar">

            <a href="#" className="brand-container">
                
                <span className="logo-text">Cited</span>
            </a>

            <div className="nav-menu">
                <div className="nav-indicator" id="nav-indicator"></div>
                <a href="#work" className="nav-link">Work</a>
                <a href="#agency" className="nav-link">Agency</a>
                <a href="#process" className="nav-link">Process</a>
                <a href="#contact" className="nav-link">Contact</a>
            </div>

            <div className="actions-container">
                <button className="btn-premium">Account</button>
                <div className="mobile-toggle">
                    <i className="ph-bold ph-list"></i>
                </div>
            </div>

        </nav>
      </div>

      <main className="page">
        <Search />
      </main>
    </>
  )
}

export default App
