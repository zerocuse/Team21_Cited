import { Link } from "react-router-dom"

function Navbar() {
    return (
        <header className="cited-nav">
            <Link to="/">Home</Link>
            <Link to="/account">Account</Link>
        </header>
    )
}

export default Navbar;