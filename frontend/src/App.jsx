import { useState } from 'react'

import './App.css'
import Navbar from "./Navbar"
import Account from "./Account" // Import your Account component
import Search from "./search/search"
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

function App() {
  return (
    <Router>
      <Navbar />
      
      <Routes>
        <Route path="/" element={
          <>
            <h1 className="cited">Cited.</h1>
            <p>Your personal fact checker.</p>
            <Search />
          </>
        } />
        <Route path="/account" element={<Account />} />
      </Routes>
    </Router>
  )
}

export default App