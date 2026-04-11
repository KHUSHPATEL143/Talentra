import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { User, Mail, Database, Zap, Key, Trash2, LogOut, ShieldCheck, PieChart, Camera, Check } from "lucide-react";

export default function Profile({ user, apiKey, setApiKey, onSaveKey, onClearKey, onLogout, onUpdateUser }) {
  const displayUser = user || {
    name: "Jan Doe",
    email: "jan.doe@nexus-ai.io",
    role: "Talent Intelligence Lead",
    joined: "April 2026",
    initials: "JD",
    photo: null
  };

  const [name, setName] = useState(displayUser.name);
  const [email, setEmail] = useState(displayUser.email);
  const [photo, setPhoto] = useState(displayUser.photo);
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const fileInputRef = useRef(null);

  const stats = [
    { label: "Resumes Processed", value: "1,284", icon: <Database className="text-blue-500" /> },
    { label: "Precision Matches", value: "452", icon: <Zap className="text-emerald-500" /> },
    { label: "Taxonomy Updates", value: "12", icon: <PieChart className="text-purple-500" /> },
  ];

  const handleApplyChanges = async () => {
    setIsSaving(true);
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    onUpdateUser({ name, email, photo });
    setIsSaving(false);
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 3000);
  };

  const handlePhotoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setPhoto(url);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto space-y-8 pb-20"
    >
      {/* Header Context */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 bg-white p-8 rounded-[2.5rem] shadow-xl shadow-slate-200/50 border border-slate-100">
        <div className="flex items-center gap-6">
          <div className="relative group">
            <div className="h-28 w-28 rounded-full bg-slate-950 flex items-center justify-center text-3xl font-bold text-emerald-400 border-4 border-emerald-400/20 shadow-lg overflow-hidden">
              {photo ? (
                <img src={photo} alt="Profile" className="h-full w-full object-cover" />
              ) : (
                displayUser.initials
              )}
            </div>
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="absolute inset-0 flex items-center justify-center bg-black/40 text-white opacity-0 group-hover:opacity-100 transition-opacity rounded-full backdrop-blur-sm cursor-pointer"
            >
              <Camera size={24} />
            </button>
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handlePhotoChange} 
              className="hidden" 
              accept="image/*"
            />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900 font-display italic tracking-tight">{displayUser.name}</h1>
            <p className="text-slate-500 font-medium flex items-center gap-2">
              <ShieldCheck size={16} className="text-emerald-500" />
              {displayUser.role || "Talent Intelligence Lead"}
            </p>
            <p className="text-xs text-slate-400 mt-2 uppercase tracking-widest font-bold">Member since {displayUser.joined || "April 2026"}</p>
          </div>
        </div>
        <button
          onClick={onLogout}
          className="flex items-center gap-2 rounded-2xl bg-red-50 px-6 py-3 text-sm font-bold text-red-600 transition-all hover:bg-red-100 active:scale-95"
        >
          <LogOut size={18} />
          Sign Out
        </button>
      </div>

      {/* Main Settings Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Personal Information */}
        <section className="bg-white p-8 rounded-[2.5rem] shadow-xl shadow-slate-200/50 border border-slate-100 flex flex-col h-full">
          <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
            <User size={20} className="text-emerald-500" />
            Personal Details
          </h2>
          <div className="space-y-4 flex-1">
            <div>
              <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Full Name</label>
              <div className="mt-1 relative">
                <User size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50/50 py-3 pl-10 pr-4 text-sm font-medium outline-none focus:border-emerald-400 focus:bg-white transition-all shadow-sm"
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Work Email</label>
              <div className="mt-1 relative">
                <Mail size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50/50 py-3 pl-10 pr-4 text-sm font-medium outline-none focus:border-emerald-400 focus:bg-white transition-all shadow-sm"
                />
              </div>
            </div>
          </div>
          
          <div className="mt-8 pt-6 border-t border-slate-100 flex items-center justify-between">
            <AnimatePresence>
              {showSuccess && (
                <motion.span
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="text-sm font-bold text-emerald-600 flex items-center gap-1.5"
                >
                  <Check size={16} /> Saved
                </motion.span>
              )}
            </AnimatePresence>
            <button
              onClick={handleApplyChanges}
              disabled={isSaving}
              className="ml-auto flex items-center gap-2 rounded-2xl bg-slate-950 px-8 py-3.5 text-sm font-bold text-white transition-all hover:bg-slate-800 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-xl shadow-slate-950/10"
            >
              {isSaving ? (
                <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : null}
              {isSaving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </section>

        {/* Developer / API Key Management & Side Context */}
        <div className="space-y-8">
          <section className="bg-slate-950 p-8 rounded-[2.5rem] shadow-2xl shadow-slate-950/20 text-white">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
              <Key size={20} className="text-emerald-400" />
              Developer Access
            </h2>
            <p className="text-sm text-slate-400 mb-6 leading-relaxed">
              Manage your API keys for authenticated integration with the Garuda Intelligence Engine.
            </p>
            <div className="space-y-4">
              <div className="relative group">
                <Key size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Paste your API key here"
                  className="w-full rounded-2xl border border-slate-800 bg-slate-900/50 py-3.5 pl-10 pr-4 text-sm text-emerald-400 placeholder:text-slate-700 outline-none transition-all focus:border-emerald-500/50 focus:ring-4 focus:ring-emerald-500/5"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={onSaveKey}
                  className="flex-1 rounded-2xl bg-emerald-500 py-3.5 text-sm font-bold text-slate-950 transition-all hover:bg-emerald-400 active:scale-95"
                >
                  Sync & Save
                </button>
                <button
                  onClick={onClearKey}
                  className="h-12 w-12 rounded-2xl bg-slate-800 flex items-center justify-center text-slate-400 transition-all hover:bg-red-500/10 hover:text-red-500 active:scale-95 border border-slate-700"
                  title="Clear Key"
                >
                  <Trash2 size={20} />
                </button>
              </div>
            </div>
          </section>

          <div className="grid grid-cols-3 gap-4">
            {stats.map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1 }}
                className="bg-white p-4 rounded-[1.5rem] shadow-lg shadow-slate-200/40 border border-slate-100 flex flex-col items-center text-center"
              >
                <div className="h-8 w-8 rounded-lg bg-slate-50 flex items-center justify-center mb-2">
                  {stat.icon}
                </div>
                <p className="text-lg font-bold text-slate-950 font-display italic">{stat.value}</p>
                <p className="text-[10px] uppercase font-bold text-slate-400 tracking-tighter">{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
