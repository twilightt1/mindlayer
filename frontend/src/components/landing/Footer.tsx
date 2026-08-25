"use client";

import Link from "next/link";

const footerLinks = {
  Product: [
    { label: "Features", href: "#features" },
    { label: "Pricing", href: "#pricing" },
    { label: "Integrations", href: "/integrations" },
    { label: "Changelog", href: "/changelog" },
  ],
  Company: [
    { label: "About", href: "/about" },
    { label: "Blog", href: "/blog" },
    { label: "Careers", href: "/careers" },
    { label: "Contact", href: "/contact" },
  ],
  Resources: [
    { label: "Documentation", href: "/docs" },
    { label: "API", href: "/api" },
    { label: "Community", href: "/community" },
    { label: "Support", href: "/support" },
  ],
  Legal: [
    { label: "Privacy", href: "/privacy" },
    { label: "Terms", href: "/terms" },
    { label: "Security", href: "/security" },
  ],
};

export function Footer() {
  return (
    <footer className="bg-white dark:bg-black border-t border-slate-100 dark:border-slate-800">
      <div className="container mx-auto px-6 py-16">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          {/* Brand */}
          <div className="col-span-2">
            <Link href="/" className="inline-block mb-4">
              <span className="text-lg font-semibold text-slate-900 dark:text-white tracking-tight">
                MindLayer
              </span>
            </Link>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6 max-w-xs leading-relaxed">
              Transform scattered information into connected knowledge.
            </p>
            {/* Social links - minimal */}
            <div className="flex gap-4">
              <a
                href="https://twitter.com/mindlayer"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              >
                Twitter
              </a>
              <a
                href="https://github.com/mindlayer"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              >
                GitHub
              </a>
              <a
                href="https://linkedin.com/company/mindlayer"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              >
                LinkedIn
              </a>
            </div>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title}>
              <h4 className="text-sm font-medium text-slate-900 dark:text-white mb-4">
                {title}
              </h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link.label}>
                    <Link
                      href={link.href}
                      className="text-sm text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom */}
        <div className="pt-8 border-t border-slate-100 dark:border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-slate-400 dark:text-slate-500">
            © 2025 MindLayer. All rights reserved.
          </p>
          <div className="flex items-center gap-2 text-sm text-slate-400 dark:text-slate-500">
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
            All systems operational
          </div>
        </div>
      </div>
    </footer>
  );
}
