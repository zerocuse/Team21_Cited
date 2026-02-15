import { useState } from 'react'
import './App.css'
import Navbar from "./Navbar"
import Account from "./Account"
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Settings from './Settings'
import SearchUpdated from './SearchUpdated/SearchUpdated'

function App() {
  return (
    <Router>
      <div className="app-container">
        <Navbar />
        
        <Routes>
          <Route path="/" element={
            <div className="hero-section">
              <div className="hero">
                <h1 className="cited">Cited.</h1>
                <p>Your personal fact checker.</p>
              </div>
              <SearchUpdated />
            </div>
          } />
          <Route path="/account" element={<Account />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App