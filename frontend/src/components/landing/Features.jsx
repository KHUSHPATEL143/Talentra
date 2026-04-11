import { motion } from "framer-motion";
import { FileSearch, Layers, Target, Database, BarChart3, ShieldCheck } from "lucide-react";

const features = [
  {
    name: "Semantic Parsing",
    description: "Go beyond keyword matching. Our AI understands context, nuance, and implied expertise within any resume format.",
    icon: FileSearch,
    color: "text-emerald-600",
    bg: "bg-emerald-50",
  },
  {
    name: "Skill Normalization",
    description: "Automated mapping to a standard skill taxonomy. Turn 'React JS', 'React.js', and 'React' into a single intelligence point.",
    icon: Layers,
    color: "text-sky-600",
    bg: "bg-sky-50",
  },
  {
    name: "Precision Matching",
    description: "Sophisticated scoring algorithms that weigh skills, experience, and domain expertise against specific job requirements.",
    icon: Target,
    color: "text-purple-600",
    bg: "bg-purple-50",
  },
  {
    name: "Taxonomy Browser",
    description: "Explore and manage your organization's skill ecosystem with a deeply hierarchical and searchable taxonomy engine.",
    icon: Database,
    color: "text-amber-600",
    bg: "bg-amber-50",
  },
  {
    name: "Actionable Insights",
    description: "Visual dashboards and candidate comparison matrices that highlight top talent at a glance.",
    icon: BarChart3,
    color: "text-rose-600",
    bg: "bg-rose-50",
  },
  {
    name: "Enterpise Security",
    description: "End-to-end encryption and API-key protected routes ensure your sensitive candidate data remains strictly confidential.",
    icon: ShieldCheck,
    color: "text-indigo-600",
    bg: "bg-indigo-50",
  },
];

export default function Features() {
  return (
    <div id="features" className="py-24 sm:py-32 bg-white rounded-[3rem] shadow-sm border border-slate-100 mx-6">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-base font-bold leading-7 text-emerald-600 uppercase tracking-widest">Capabilities</h2>
          <p className="mt-2 font-display text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Everything you need for <span className="text-slate-400">intelligent talent intake.</span>
          </p>
          <p className="mt-6 text-lg leading-8 text-slate-600">
            Garuda replaces legacy parsing engines with a modern, LLM-orchestrated pipeline that handles the heavy lifting of candidate evaluation.
          </p>
        </div>
        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
            {features.map((feature, index) => (
              <motion.div 
                key={feature.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="flex flex-col group"
              >
                <dt className="flex items-center gap-x-4 text-lg font-bold leading-7 text-slate-900">
                  <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${feature.bg} ${feature.color} transition-transform group-hover:scale-110 group-hover:rotate-3`}>
                    <feature.icon size={24} aria-hidden="true" />
                  </div>
                  {feature.name}
                </dt>
                <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-slate-600">
                  <p className="flex-auto">{feature.description}</p>
                </dd>
              </motion.div>
            ))}
          </dl>
        </div>
      </div>
    </div>
  );
}
