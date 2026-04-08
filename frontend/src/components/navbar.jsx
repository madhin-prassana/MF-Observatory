import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (path) => location.pathname === path;

  const navLinks = [
    { path: '/', label: 'Home' },
    { path: '/explorer', label: 'Explore Funds' },
    { path: '/analytics', label: 'Analytics' },
  ];

  const linkClasses = (path) =>
    `px-4 py-2 rounded-sm text-xs font-bold tracking-[0.05em] uppercase transition-all duration-200 border ${
      isActive(path)
        ? 'bg-arctic-sheet border-electric-cyan/30 text-electric-cyan shadow-[0_0_10px_rgba(76,215,246,0.1)]'
        : 'border-transparent text-gray-400 hover:text-white hover:bg-white/5 hover:border-white/10'
    }`;

  return (
    <nav className="bg-deep-space/95 backdrop-blur-xl border-b border-permafrost sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-8 h-8 bg-glacial-blue rounded-sm flex items-center justify-center text-deep-space font-extrabold text-sm shadow-[0_0_15px_rgba(173,198,255,0.3)] group-hover:shadow-[0_0_20px_rgba(173,198,255,0.6)] transition-shadow">
              V.
            </div>
            <div className="text-xl font-bold">
              <span className="text-white">Vantage</span>
              <span className="gradient-text"> .</span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {navLinks.map((link) => (
              <Link key={link.path} to={link.path} className={linkClasses(link.path)}>
                {link.label}
              </Link>
            ))}
          </div>

          {/* Mobile Hamburger */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden text-gray-300 hover:text-white p-2 rounded-lg hover:bg-white/5 transition-colors"
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Menu */}
        <div
          className={`md:hidden overflow-hidden transition-all duration-300 ease-in-out ${
            mobileOpen ? 'max-h-60 pb-4' : 'max-h-0'
          }`}
        >
          <div className="flex flex-col space-y-1 pt-2">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setMobileOpen(false)}
                className={linkClasses(link.path)}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;