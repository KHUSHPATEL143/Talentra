import { motion, AnimatePresence } from "framer-motion";
import { X, Mail, Lock, Code, Globe, User, ShieldCheck } from "lucide-react";

export default function AuthModal({ isOpen, onClose, type = "login", onSuccess }) {
  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const name = formData.get("name") || "Jan Doe";
    const email = formData.get("email");
    
    // In a real app, we'd check if password matches confirmPassword here
    if (onSuccess) {
      onSuccess({ name, email });
    }
  };

  const isSignUp = type === "signup";

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"
        />
        
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-md overflow-hidden rounded-[2.5rem] bg-white p-8 shadow-2xl"
        >
          <button
            onClick={onClose}
            className="absolute right-6 top-6 text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X size={20} />
          </button>

          <div className="text-center">
            <h2 className="font-display text-3xl font-bold text-slate-900">
              {isSignUp ? "Create Account" : "Welcome Back"}
            </h2>
            <p className="mt-2 text-slate-500">
              {isSignUp 
                ? "Join Talentra and start transforming your recruitment workflow."
                : "Enter your credentials to access your talent intelligence."}
            </p>
          </div>

          <div className="mt-8 space-y-4">
            <button className="flex w-full items-center justify-center gap-3 rounded-2xl border border-slate-200 py-3 text-sm font-bold text-slate-700 transition-all hover:bg-slate-50 active:scale-[0.98]">
              <Globe size={20} className="text-red-500" />
              Continue with Google
            </button>
            <button className="flex w-full items-center justify-center gap-3 rounded-2xl border border-slate-200 py-3 text-sm font-bold text-slate-700 transition-all hover:bg-slate-50 active:scale-[0.98]">
              <Code size={20} />
              Continue with GitHub
            </button>
          </div>

          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-4 text-slate-400 font-bold tracking-widest">Or email</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignUp && (
              <div className="relative">
                <User size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  name="name"
                  required
                  placeholder="Full name"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50/50 py-3 pl-12 pr-4 text-sm outline-none transition-all focus:border-emerald-400 focus:bg-white focus:ring-4 focus:ring-emerald-400/10"
                />
              </div>
            )}
            
            <div className="relative">
              <Mail size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="email"
                name="email"
                required
                placeholder="Work email"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50/50 py-3 pl-12 pr-4 text-sm outline-none transition-all focus:border-emerald-400 focus:bg-white focus:ring-4 focus:ring-emerald-400/10"
              />
            </div>

            <div className="relative">
              <Lock size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="password"
                required
                minLength={6}
                placeholder="Password"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-12 pr-4 text-sm outline-none transition-all focus:border-emerald-400 focus:bg-white focus:ring-4 focus:ring-emerald-400/10"
              />
            </div>

            {isSignUp && (
              <div className="relative">
                <ShieldCheck size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="password"
                  required
                  placeholder="Confirm password"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-12 pr-4 text-sm outline-none transition-all focus:border-emerald-400 focus:bg-white focus:ring-4 focus:ring-emerald-400/10"
                />
              </div>
            )}

            <button
              type="submit"
              className="mt-2 w-full rounded-2xl bg-slate-950 py-4 text-base font-bold text-white transition-all hover:bg-slate-800 active:scale-[0.98] shadow-xl shadow-slate-950/10"
            >
              {isSignUp ? "Create Account" : "Sign In"}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-slate-500">
            {type === "login" ? "Don't have an account?" : "Already have an account?"}
            <button className="ml-1 font-bold text-emerald-600 hover:text-emerald-700">
              {type === "login" ? "Sign up" : "Log in"}
            </button>
          </p>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
