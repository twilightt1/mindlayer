"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { GradientText } from "@/components/ui/BackgroundEffects";

const plans = [
  {
    name: "Free",
    description: "For individuals getting started",
    price: 0,
    features: [
      "3 document sources",
      "100 queries per month",
      "Basic search",
      "1 workspace",
    ],
    cta: "Get started",
    popular: false,
  },
  {
    name: "Pro",
    description: "For teams and power users",
    price: 29,
    features: [
      "Unlimited sources",
      "Unlimited queries",
      "AI insights",
      "Team collaboration",
      "Priority support",
    ],
    cta: "Start free trial",
    popular: true,
  },
  {
    name: "Enterprise",
    description: "For large organizations",
    price: 99,
    features: [
      "Everything in Pro",
      "Unlimited team seats",
      "Custom integrations",
      "SSO & SAML",
      "Dedicated support",
    ],
    cta: "Contact sales",
    popular: false,
  },
];

export function PricingSection() {
  return (
    <section id="pricing" className="relative py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-background" />
      
      {/* Gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-violet-500/5 to-transparent" />

      <div className="relative z-10 container mx-auto px-6">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-2xl mx-auto text-center mb-20"
        >
          <motion.span 
            className="text-xs tracking-[0.2em] uppercase text-violet-400 mb-4 block"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
          >
            Pricing
          </motion.span>
          
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tighter text-white mb-6">
            Simple, transparent
            <br />
            <span className="text-white/50">pricing</span>
          </h2>
          
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-lg text-white/40"
          >
            Start free, upgrade when you're ready.
          </motion.p>
        </motion.div>

        {/* Pricing cards */}
        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              whileHover={{ y: -5 }}
              className={`relative p-8 rounded-2xl backdrop-blur-sm transition-all duration-300 ${
                plan.popular
                  ? 'border border-violet-500/50 bg-gradient-to-b from-violet-500/10 to-transparent'
                  : 'border border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20'
              }`}
            >
              {plan.popular && (
                <motion.div 
                  className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 text-xs font-bold uppercase tracking-wider bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-full shadow-lg shadow-violet-500/25"
                  initial={{ scale: 0.8 }}
                  whileInView={{ scale: 1 }}
                  viewport={{ once: true }}
                >
                  Most popular
                </motion.div>
              )}

              <div className="mb-6">
                <h3 className="text-lg font-bold text-white mb-1">
                  {plan.name}
                </h3>
                <p className="text-sm text-white/40">
                  {plan.description}
                </p>
              </div>

              <div className="mb-8">
                <span className="text-5xl font-black text-white">
                  ${plan.price}
                </span>
                {plan.price > 0 && (
                  <span className="text-white/40">/month</span>
                )}
              </div>

              <Link
                href="/signup"
                className={`block w-full py-3 text-center font-semibold rounded-full transition-all duration-300 ${
                  plan.popular
                    ? 'bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-500 hover:to-purple-500 shadow-lg shadow-violet-500/25'
                    : 'bg-white/10 text-white hover:bg-white/20'
                } cursor-pointer`}
              >
                {plan.cta}
              </Link>

              <ul className="mt-8 space-y-3">
                {plan.features.map((feature, i) => (
                  <motion.li 
                    key={feature} 
                    className="flex items-center gap-3 text-sm text-white/60"
                    initial={{ opacity: 0, x: -10 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.3 + i * 0.05 }}
                  >
                    <span className="w-1.5 h-1.5 bg-gradient-to-r from-violet-500 to-purple-500 rounded-full" />
                    {feature}
                  </motion.li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>

        {/* Footer note */}
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mt-12 text-center text-sm text-white/40"
        >
          All plans include a 14-day free trial. No credit card required.
        </motion.p>
      </div>
    </section>
  );
}
