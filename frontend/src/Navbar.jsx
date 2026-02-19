import { Link } from "react-router-dom";
import { useEffect, useRef, useState } from "react"; 
import "./Navbar.css";

function Navbar() {
    const navRef = useRef(null);
    const indicatorRef = useRef(null); 
    const [menuOpen, setMenuOpen] = useState(false);
    const [premiumOpen, setPremiumOpen] = useState(false);

    useEffect(() => {
        const navbar = navRef.current;
        if (!navbar) return;

        const handleNavHover = (e) => {
            const indicator = indicatorRef.current;
            if (indicator && e.target.classList.contains('nav-link')) {
                const linkRect = e.target.getBoundingClientRect();
                const menuRect = e.target.parentElement.getBoundingClientRect();
                const left = linkRect.left - menuRect.left;
                
                indicator.style.width = `${linkRect.width}px`;
                indicator.style.transform = `translateX(${left}px)`;
                indicator.style.opacity = '1';
            }
        };

        const handleNavLeave = () => {
            if (indicatorRef.current) indicatorRef.current.style.opacity = '0';
        };

        navbar.addEventListener('mouseover', handleNavHover);
        navbar.addEventListener('mouseleave', handleNavLeave);
        
        return () => {
            navbar.removeEventListener('mouseover', handleNavHover);
            navbar.removeEventListener('mouseleave', handleNavLeave);
        };
    }, [menuOpen]); 

    return (
        <div className="stage">
            <nav className="navbar-card" ref={navRef}>
                
                <div 
                    className="nav-dropdown" 
                    onMouseEnter={() => setMenuOpen(true)} 
                    onMouseLeave={() => setMenuOpen(false)}
                >
                    <div className={`hamburger ${menuOpen ? 'open' : ''}`}>
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                    
                    {menuOpen && (
                        <div className="nav-menu">
                            
                            <div className="nav-indicator" ref={indicatorRef}></div>
                            <a href="#work" className="nav-link">Work</a>
                            <a href="#agency" className="nav-link">Agency</a>
                            <a href="#process" className="nav-link">Process</a>
                            <a href="#contact" className="nav-link">Contact</a>
                        </div>
                    )}
                </div>

                <Link to="/" id="logo_link" style={{ textDecoration: 'none' }}>
                    <span className="logo-text">Cited.</span>
                </Link>

                <div className="actions-container">
                    <div 
                        className="premium-dropdown"
                        onMouseEnter={() => setPremiumOpen(true)}
                        onMouseLeave={() => setPremiumOpen(false)}
                    >
                        <div className="btn-premium">
                            <img id="acc-icon" src="./src/assets/account_icon.svg" alt="account" />
                            Account
                        </div>
                        
                        {premiumOpen && (
                            <div className="premium-menu">
                                <Link to="/account" className="dropdown-item">Profile</Link>
                                <Link to="/settings" className="dropdown-item">Settings</Link>
                                <hr className="dropdown-divider" />
                                <Link to="/logout" className="dropdown-item">Log Out</Link>
                            </div>
                        )}
                    </div>
                </div>
            </nav>
        </div>
    );
}

export default Navbar;