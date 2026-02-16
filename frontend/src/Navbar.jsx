import { Link } from "react-router-dom";
import { useEffect, useRef } from "react";
import "./Navbar.css";

function Navbar() {
    const navRef = useRef(null);
    const indicatorRef = useRef(null); 

    useEffect(() => {
        const navbar = navRef.current;
        const indicator = indicatorRef.current;
        if (!navbar || !indicator) return;

        const handleMouseMove = (e) => {
            const rect = navbar.getBoundingClientRect();
            navbar.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
            navbar.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
        };

        const handleNavHover = (e) => {
            if (e.target.classList.contains('nav-link')) {
                const linkRect = e.target.getBoundingClientRect();
                const menuRect = e.target.parentElement.getBoundingClientRect();
                const left = linkRect.left - menuRect.left;
                
                indicator.style.width = `${linkRect.width}px`;
                indicator.style.transform = `translateX(${left}px)`;
                indicator.style.opacity = '1';
            }
        };

        const handleNavLeave = () => {
            indicator.style.opacity = '0';
        };

        window.addEventListener('mousemove', handleMouseMove);
        navbar.addEventListener('mouseover', handleNavHover);
        navbar.addEventListener('mouseleave', handleNavLeave);
        
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            navbar.removeEventListener('mouseover', handleNavHover);
            navbar.removeEventListener('mouseleave', handleNavLeave);
        };
    }, []);

    return (
        <>
        <div className="stage">
            <nav className="navbar-card" ref={navRef}>
                <Link to="/" className="brand-container">
                    <span className="logo-text">Cited.</span>
                </Link>

                <div className="nav-menu">
                    
                    <div className="nav-indicator" ref={indicatorRef}></div>
                    <a href="#work" className="nav-link">Work</a>
                    <a href="#agency" className="nav-link">Agency</a>
                    <a href="#process" className="nav-link">Process</a>
                    <a href="#contact" className="nav-link">Contact</a>
                </div>

                <div className="actions-container">
                    <Link to="/account" className="btn-premium"><img id="acc-icon"src="./src/assets/account_icon.svg" alt="account"/>Log In</Link>
                </div>
            </nav>
        </div>

        <header className="cited-nav">
            <div className="nav-left">
                <Link to="/"><img src="./src/assets/home_icon.svg" alt="home" /></Link>
            </div>
            <div className="nav-right">
                <Link to="/account"><img src="./src/assets/account_icon.svg" alt="account"/></Link>
                <Link to="/settings"><img src="./src/assets/settings_icon.svg" alt="settings" className="settings-icon" /></Link>
            </div>
        </header>
        </>
    );
}

export default Navbar;