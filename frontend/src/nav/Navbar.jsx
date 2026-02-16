import React from "react";
import "./Navbar.css";


const Navbar = () => {
  return (
    <div class="stage">
        <nav id="navbar">
        <div class="nav-container">
            <div class="logo">WPDean</div>
            <ul class="nav-menu">
                <li class="nav-item">
                    <a href="#" class="nav-link">Home</a>
                </li>
                <li class="nav-item">
                    <a href="#" class="nav-link dropdown-toggle">Solutions</a>
                    <ul class="dropdown-menu">
                        <li class="dropdown-item">
                            <a href="#" class="dropdown-link dropdown-toggle">Cloud Services</a>
                            <ul class="dropdown-menu">
                                <li class="dropdown-item"><a href="#" class="dropdown-link">Infrastructure</a></li>
                                <li class="dropdown-item"><a href="#" class="dropdown-link">Platform</a></li>
                                <li class="dropdown-item"><a href="#" class="dropdown-link">Software</a></li>
                                <li class="dropdown-item"><a href="#" class="dropdown-link">Security</a></li>
                            </ul>
                        </li>
                        <li class="dropdown-item">
                            <a href="#" class="dropdown-link dropdown-toggle">AI & Analytics</a>
                            <ul class="dropdown-menu">
                                <li class="dropdown-item"><a href="#" class="dropdown-link">Machine Learning</a></li>
                                <li class="dropdown-item"><a href="#" class="dropdown-link">Data Science</a></li>
                                <li class="dropdown-item"><a href="#" class="dropdown-link">Business Intelligence</a></li>
                            </ul>
                        </li>
                        <li class="dropdown-item"><a href="#" class="dropdown-link">Cybersecurity</a></li>
                        <li class="dropdown-item"><a href="#" class="dropdown-link">DevOps</a></li>
                    </ul>
                </li>
                <li class="nav-item">
                    <a href="#" class="nav-link dropdown-toggle">Industries</a>
                    <ul class="dropdown-menu">
                        <li class="dropdown-item"><a href="#" class="dropdown-link">Finance</a></li>
                        <li class="dropdown-item"><a href="#" class="dropdown-link">Healthcare</a></li>
                        <li class="dropdown-item"><a href="#" class="dropdown-link">Retail</a></li>
                        <li class="dropdown-item"><a href="#" class="dropdown-link">Manufacturing</a></li>
                    </ul>
                </li>
                <li class="nav-item">
                    <a href="#" class="nav-link dropdown-toggle">Resources</a>
                    <ul class="dropdown-menu">
                        <li class="dropdown-item"><a href="#" class="dropdown-link">Documentation</a></li>
                        <li class="dropdown-item"><a href="#" class="dropdown-link">Case Studies</a></li>
                        <li class="dropdown-item"><a href="#" class="dropdown-link">Blog</a></li>
                        <li class="dropdown-item"><a href="#" class="dropdown-link">Support</a></li>
                    </ul>
                </li>
                <li class="nav-item">
                    <a href="#" class="nav-link">Pricing</a>
                </li>
            </ul>
        </div>
    </nav>
    </div>
  );
};

export default Navbar;
