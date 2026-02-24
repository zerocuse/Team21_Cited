import { Link } from "react-router-dom"

import "./Navbar.css"

function Navbar() {
    return (
        <header className="cited-nav">
            <div className="nav-left">
                <Link to="/"><img src="./src/assets/home_icon.svg" alt="home" /></Link>
            </div>
            <div className="nav-right">
                <Link to="/account"><img src="./src/assets/account_icon.svg" alt="account"/></Link>
                <Link to="/settings"><img src="./src/assets/settings_icon.svg" alt="settings" className="settings-icon" /></Link>
            </div>
        </header>
    )
}

export default Navbar;