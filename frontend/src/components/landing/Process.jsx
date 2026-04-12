import { motion } from "framer-motion";
import { UploadCloud, Search, CheckCircle2 } from "lucide-react";

export default function Process({ onGetStarted }) {
  const steps = [
    {
      name: "Upload & Ingest",
      description: "Simply drop your resumes in any format (PDF, DOCX, etc.). Our ingestion layer handles the initial processing and cleaning.",
      icon: UploadCloud,
      color: "text-emerald-600",
      bg: "bg-emerald-100",
    },
    {
      name: "AI Extraction",
      description: "Our high-order LLMs extract skills, experience, and metadata, mapping them to the standard Talentra taxonomy.",
      icon: Search,
      color: "text-sky-600",
      bg: "bg-sky-100",
    },
    {
      name: "Match & Rank",
      description: "Instantly score candidates against your job requirements using our semantic matching algorithms.",
      icon: CheckCircle2,
      color: "text-purple-600",
      bg: "bg-purple-100",
    },
  ];

  return (
    <div className="py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-base font-bold leading-7 text-emerald-600 uppercase tracking-widest">Efficiency</h2>
          <p className="mt-2 font-display text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            How Talentra <span className="text-slate-400">works for you.</span>
          </p>
        </div>
        
        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <div className="grid grid-cols-1 gap-y-12 lg:grid-cols-3 lg:gap-x-12">
            {steps.map((step, index) => (
              <motion.div 
                key={step.name}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.2 }}
                className="relative flex flex-col items-center text-center group"
              >
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-12 left-[60%] w-[80%] border-t-2 border-dashed border-slate-200 -z-10" />
                )}
                <div className={`flex h-24 w-24 items-center justify-center rounded-3xl ${step.bg} ${step.color} mb-8 ring-8 ring-white shadow-xl transition-all group-hover:scale-110 group-hover:rotate-6`}>
                  <step.icon size={40} />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">{step.name}</h3>
                <p className="text-slate-600 leading-relaxed max-w-xs">{step.description}</p>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="mt-20 flex justify-center">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="rounded-3xl bg-slate-100 p-8 text-center max-w-3xl border border-slate-200/50"
          >
            <p className="text-slate-700 italic font-medium leading-relaxed">
              "Talentra has reduced our initial screening time by over 80%. The accuracy of the skill extraction is far superior to any legacy parser we've used."
            </p>
            <div className="mt-6 flex items-center justify-center gap-3">
              <div className="h-10 w-10 rounded-full bg-slate-300" />
              <div className="text-left">
                <p className="text-sm font-bold text-slate-900">Sarah Jenkins</p>
                <p className="text-xs text-slate-500">Director of Talent Acquisition, TechFlow</p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
