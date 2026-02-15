import { useState } from 'react'

import './App.css'
import Navbar from "./Navbar"
import Account from "./Account" // Import your Account component
import Search from "./search/search"
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Settings from './Settings'
import SearchUpdated from './SearchUpdated/SearchUpdated'

function App() {
  return (
    <Router>

      <SearchUpdated />

      <Navbar />
      
      <Routes>
        <Route path="/" element={
          <>
            <h1 className="cited">Cited.</h1>
            <p>Your personal fact checker.</p>
          </>
        } />
        <Route path="/account" element={<Account />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Router>
  )
}

export default App