"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

const navItems = [
  { label: "Features", href: "#features" },
  { label: "How it works", href: "#how-it-works" },
  { label: "Pricing", href: "#pricing" },
  { label: "FAQ", href: "#faq" },
];

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? "bg-white/80 dark:bg-black/80 backdrop-blur-md border-b border-slate-100 dark:border-slate-800"
          : "bg-transparent"
      }`}
    >
      <div className="container mx-auto px-6">
        <div className="flex items-center justify-between h-16 md:h-20">
          {/* Logo - Minimal text only */}
          <Link href="/" className="flex items-center">
            <span className="text-lg font-semibold tracking-tight text-slate-900 dark:text-white">
              MindLayer
            </span>
          </Link>

          {/* Desktop Navigation - Minimal */}
          <div className="hidden md:flex items-center gap-8">
            {navItems.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="text-sm text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
              >
                {item.label}
              </Link>
            ))}
          </div>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              Sign in
            </Link>
            <Link
              href="/signup"
              className="px-5 py-2 text-sm font-medium bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-full transition-all duration-300 hover:bg-slate-800 dark:hover:bg-slate-100"
            >
              Start free
            </Link>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 -mr-2"
          >
            <span className="sr-only">Menu</span>
            {isMobileMenuOpen ? (
              <span className="block w-5 h-5 text-slate-900 dark:text-white font-light">×</span>
            ) : (
              <span className="block w-5 h-5 text-slate-900 dark:text-white">☰</span>
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-white dark:bg-black border-t border-slate-100 dark:border-slate-800"
          >
            <div className="container mx-auto px-6 py-6 space-y-4">
              {navItems.map((item) => (
                <Link
                  key={item.label}
                  href={item.href}
                  className="block text-base text-slate-600 dark:text-slate-400"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
              <hr className="border-slate-100 dark:border-slate-800" />
              <Link
                href="/login"
                className="block text-base text-slate-600 dark:text-slate-400"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Sign in
              </Link>
              <Link
                href="/signup"
                className="block text-base font-medium text-slate-900 dark:text-white"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Start free →
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
