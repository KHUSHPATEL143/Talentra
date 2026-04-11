import { motion } from "framer-motion";
import { ArrowRight, Sparkles, Shield, Zap } from "lucide-react";

export default function Hero({ onGetStarted }) {
  return (
    <div className="relative overflow-hidden pt-16 pb-24 lg:pt-24 lg:pb-32">
      {/* Background Decorative Elements */}
      <div className="absolute top-0 left-1/2 -z-10 h-[1000px] w-[1000px] -translate-x-1/2 [mask-image:radial-gradient(closest-side,white,transparent)] sm:top-[-200px]">
        <div className="absolute inset-0 bg-gradient-to-r from-emerald-400/20 to-sky-400/20 opacity-40 blur-3xl" />
      </div>

      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="lg:grid lg:grid-cols-2 lg:gap-x-12 lg:items-center">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="max-w-2xl"
          >
            <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-600 ring-1 ring-inset ring-emerald-600/20 mb-8">
              <Sparkles size={14} />
              <span>AI-Powered Resume Intelligence</span>
            </div>
            <h1 className="font-display text-5xl font-extrabold tracking-tight text-slate-900 sm:text-6xl leading-[1.1]">
              Turn Unstructured Resumes Into <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 to-sky-600">Pure Intelligence.</span>
            </h1>
            <p className="mt-8 text-lg leading-8 text-slate-600">
              GARUDA leverages high-order LLMs to parse, normalize, and match candidates with unprecedented precision. Stop scanning documents and start making data-driven talent decisions.
            </p>
            <div className="mt-10 flex items-center gap-x-6">
              <button
                onClick={onGetStarted}
                className="group relative inline-flex items-center gap-2 rounded-full bg-slate-950 px-8 py-4 text-sm font-bold text-white transition-all hover:bg-slate-800 hover:shadow-xl hover:shadow-emerald-950/20 active:scale-95"
              >
                Start Parsing Now
                <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
              </button>
              <a href="#features" className="text-sm font-bold leading-6 text-slate-900 hover:text-emerald-600 transition-colors">
                Learn how it works <span aria-hidden="true">→</span>
              </a>
            </div>

            <div className="mt-12 grid grid-cols-3 gap-8 border-t border-slate-200 pt-8">
              <div>
                <dt className="flex items-center gap-2 text-sm font-semibold text-slate-600">
                  <Zap size={16} className="text-emerald-500" /> Speed
                </dt>
                <dd className="mt-1 text-2xl font-bold text-slate-900">2s / Resume</dd>
              </div>
              <div>
                <dt className="flex items-center gap-2 text-sm font-semibold text-slate-600">
                  <Shield size={16} className="text-sky-500" /> Accuracy
                </dt>
                <dd className="mt-1 text-2xl font-bold text-slate-900">99.4%</dd>
              </div>
              <div>
                <dt className="text-sm font-semibold text-slate-600">Processed</dt>
                <dd className="mt-1 text-2xl font-bold text-slate-900">240k+</dd>
              </div>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="mt-16 lg:mt-0 relative group"
          >
            <div className="relative rounded-3xl bg-slate-900/5 p-2 ring-1 ring-inset ring-slate-900/10 lg:-m-4 lg:rounded-[2.5rem] lg:p-4 backdrop-blur-sm">
              <img
                src="/assets/hero.png"
                alt="App screenshot"
                className="rounded-2xl shadow-2xl ring-1 ring-slate-900/10 transition-transform duration-700 group-hover:scale-[1.02]"
              />
              {/* Floating Badge */}
              <div className="absolute -bottom-6 -left-6 rounded-2xl bg-white p-4 shadow-xl shadow-slate-900/10 border border-slate-100 flex items-center gap-3 animate-bounce-slow">
                <div className="h-10 w-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
                  <Sparkles size={20} />
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-500 uppercase">Latest Match</p>
                  <p className="text-sm font-bold text-slate-900">Senior AI Engineer • 98% Fit</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
