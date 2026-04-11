import { motion } from "framer-motion";
import { Check } from "lucide-react";

const tiers = [
  {
    name: "Starter",
    price: "$0",
    description: "Perfect for exploring AI resume intelligence.",
    features: ["50 Resumes / mo", "Standard Taxonomy", "Basic Matching", "Community Support"],
    buttonText: "Start Free",
    featured: false,
  },
  {
    name: "Professional",
    price: "$79",
    description: "Ideal for growing recruitment teams.",
    features: ["2,000 Resumes / mo", "Advanced Hierarchical Taxonomy", "Precision Matching", "Priority Email Support", "API Access"],
    buttonText: "Get Started",
    featured: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    description: "For organizations with high-volume needs.",
    features: ["Unlimited Resumes", "Custom Taxonomy Design", "Dedicated AI Agent Tuning", "SLA & 24/7 Support", "On-premise Deployment"],
    buttonText: "Contact Sales",
    featured: false,
  },
];

export default function Pricing() {
  return (
    <div className="py-24 sm:py-32 bg-slate-50 relative overflow-hidden">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-base font-bold leading-7 text-emerald-600 uppercase tracking-widest">Pricing</h2>
          <p className="mt-2 font-display text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Scalable intelligence for <span className="text-slate-400">every team.</span>
          </p>
        </div>
        
        <div className="mx-auto mt-16 grid max-w-lg grid-cols-1 gap-y-6 lg:max-w-none lg:grid-cols-3 lg:gap-x-8">
          {tiers.map((tier, index) => (
            <motion.div
              key={tier.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={`relative flex flex-col rounded-3xl p-8 shadow-xl transition-all hover:scale-[1.02] ${
                tier.featured 
                  ? "bg-slate-950 text-white ring-4 ring-emerald-500/20 z-10" 
                  : "bg-white text-slate-900 ring-1 ring-slate-200"
              }`}
            >
              <div className="mb-8">
                <h3 className={`text-lg font-bold ${tier.featured ? "text-emerald-400" : "text-emerald-600"}`}>
                  {tier.name}
                </h3>
                <div className="mt-4 flex items-baseline gap-x-2">
                  <span className="text-5xl font-extrabold tracking-tight">{tier.price}</span>
                  {tier.price !== "Custom" && <span className="text-sm font-semibold opacity-60">/month</span>}
                </div>
                <p className={`mt-6 text-sm leading-6 ${tier.featured ? "text-slate-300" : "text-slate-500"}`}>
                  {tier.description}
                </p>
              </div>
              
              <ul className="space-y-4 mb-10 flex-1">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-3 text-sm">
                    <Check size={18} className={tier.featured ? "text-emerald-400" : "text-emerald-600"} />
                    <span className={tier.featured ? "text-slate-200" : "text-slate-600"}>{feature}</span>
                  </li>
                ))}
              </ul>
              
              <button
                className={`w-full rounded-2xl py-4 text-sm font-bold transition-all active:scale-95 ${
                  tier.featured 
                    ? "bg-white text-slate-950 hover:bg-emerald-50" 
                    : "bg-slate-950 text-white hover:bg-slate-800"
                }`}
              >
                {tier.buttonText}
              </button>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
