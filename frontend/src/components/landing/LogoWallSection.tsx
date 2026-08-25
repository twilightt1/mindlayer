"use client";

import { motion } from "framer-motion";

const logos = [
  { name: "Stripe", slug: "stripe" },
  { name: "Vercel", slug: "vercel" },
  { name: "Linear", slug: "linear" },
  { name: "Notion", slug: "notion" },
  { name: "Figma", slug: "figma" },
  { name: "GitHub", slug: "github" },
];

// Simple SVG logo components using Simple Icons style
const LogoIcon = ({ slug, name }: { slug: string; name: string }) => {
  // Generate a simple geometric logo mark based on the name
  const initial = name.charAt(0);
  const colors: Record<string, string> = {
    stripe: "#6772e5",
    vercel: "#ffffff",
    linear: "#5e6ad2",
    notion: "#ffffff",
    figma: "#f24e1e",
    github: "#ffffff",
  };

  return (
    <div className="flex items-center justify-center w-full h-full">
      <svg
        viewBox="0 0 100 100"
        className="w-12 h-12"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle cx="50" cy="50" r="40" fill={colors[slug] || "#ffffff"} fillOpacity="0.2" />
        <text
          x="50"
          y="50"
          textAnchor="middle"
          dominantBaseline="central"
          fill={colors[slug] || "#ffffff"}
          fontSize="36"
          fontWeight="bold"
          fontFamily="system-ui, sans-serif"
        >
          {initial}
        </text>
      </svg>
    </div>
  );
};

export function LogoWallSection() {
  return (
    <section className="relative py-20 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-background" />
      
      <div className="relative z-10 container mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto"
        >
          <div className="grid grid-cols-3 md:grid-cols-6 gap-8 items-center justify-items-center">
            {logos.map((logo, index) => (
              <motion.div
                key={logo.name}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="w-16 h-16 flex items-center justify-center"
                title={logo.name}
              >
                <LogoIcon slug={logo.slug} name={logo.name} />
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
