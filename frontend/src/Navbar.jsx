import { Link } from "react-router-dom"

import "./Navbar.css"

function Navbar() {
    return (
        <header className="cited-nav">
            <Link to="/"><img src="./src/assets/home_icon.svg" alt="home" /></Link>
            <Link to="/account"><img src="./src/assets/account_icon.svg" alt="account" /></Link>
            <Link to="/settings"><img src="./src/assets/settings_icon.svg" alt="settings" /></Link>
        </header>
    )
}

export default Navbar;