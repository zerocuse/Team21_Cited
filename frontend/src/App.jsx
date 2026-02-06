import { useState } from 'react'

import './App.css'
import Search from "./search/search"

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
    
    <Search />
    </>
  )
}

export default App
