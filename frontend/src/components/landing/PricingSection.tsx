"use client";

import { motion } from "framer-motion";
import Link from "next/link";

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
      <div className="absolute inset-0 bg-white dark:bg-black" />
      
      <div className="relative z-10 container mx-auto px-6">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-2xl mx-auto text-center mb-20"
        >
          <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-slate-900 dark:text-white mb-6">
            Simple, transparent pricing
          </h2>
          <p className="text-lg text-slate-500 dark:text-slate-400">
            Start free, upgrade when you're ready.
          </p>
        </motion.div>

        {/* Pricing cards */}
        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={`relative p-8 bg-white dark:bg-slate-900 border rounded-2xl ${
                plan.popular 
                  ? 'border-slate-900 dark:border-white shadow-lg' 
                  : 'border-slate-100 dark:border-slate-800'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-medium rounded-full">
                  Most popular
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-1">
                  {plan.name}
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {plan.description}
                </p>
              </div>

              <div className="mb-8">
                <span className="text-4xl font-semibold text-slate-900 dark:text-white">
                  ${plan.price}
                </span>
                {plan.price > 0 && (
                  <span className="text-slate-500 dark:text-slate-400">/month</span>
                )}
              </div>

              <Link
                href="/signup"
                className={`block w-full py-3 text-center font-medium rounded-full transition-all duration-300 ${
                  plan.popular
                    ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-slate-100'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white hover:bg-slate-200 dark:hover:bg-slate-700'
                }`}
              >
                {plan.cta}
              </Link>

              <ul className="mt-8 space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-400">
                    <span className="w-1 h-1 bg-slate-400 dark:bg-slate-600 rounded-full" />
                    {feature}
                  </li>
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
          className="mt-12 text-center text-sm text-slate-500 dark:text-slate-400"
        >
          All plans include a 14-day free trial. No credit card required.
        </motion.p>
      </div>
    </section>
  );
}
