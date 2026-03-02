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
                    <button
                        className="dropdown-toggle"
                        onClick={toggleDropdown}
                        aria-expanded={dropdownOpen}
                        aria-haspopup="true"
                    >
                        <img src="./src/assets/account_icon.svg" alt="account" />
                    </button>
                    {dropdownOpen && (
                        <ul className="dropdown-menu">
                            <li>
                                <Link
                                    to="/login"
                                    onClick={() => setDropdownOpen(false)}
                                >
                                    Login
                                </Link>
                            </li>
                            <li>
                                <Link
                                    to="/account"
                                    onClick={() => setDropdownOpen(false)}
                                >
                                    My Account
                                </Link>
                            </li>
                        </ul>
                    )}
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