import { useState, useEffect, useRef } from "react"
import { Link } from "react-router-dom"
import "./Navbar.css"

function Navbar() {
    const [dropdownOpen, setDropdownOpen] = useState(false)
    const dropdownRef = useRef(null)

    const toggleDropdown = () => {
        setDropdownOpen(prev => !prev)
    }
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setDropdownOpen(false)
            }
        }

        document.addEventListener("mousedown", handleClickOutside)
        return () => document.removeEventListener("mousedown", handleClickOutside)
    }, [])

    return (
        <header className="cited-nav">
            <div className="nav-left">
                <Link to="/">
                    <img src="./src/assets/home_icon.svg" alt="home" />
                </Link>
            </div>
            <div className="nav-right">
                <div className="dropdown" ref={dropdownRef}>
                    <Link to="/account">
                    <img src="./src/assets/account_icon.svg" alt="account" />
                    </Link>
                </div>
                <Link to="/settings">
                    <img
                        src="./src/assets/settings_icon.svg"
                        alt="settings"
                        className="settings-icon"
                    />
                </Link>
            </div>
        </header>
    )
}

export default Navbar