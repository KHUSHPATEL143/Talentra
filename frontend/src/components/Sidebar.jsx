import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { 
  LayoutDashboard, 
  UserCheck, 
  Database, 
  Cpu, 
  LogIn, 
  UserPlus, 
  Settings, 
  ChevronRight,
  LogOut
} from "lucide-react";

export default function Sidebar({ isLoggedIn, user, onLogout, onOpenAuth }) {
  const location = useLocation();

  const navItems = [
    { label: "Intake", path: "/intake", icon: LayoutDashboard },
    { label: "Match", path: "/match", icon: UserCheck },
    { label: "Taxonomy", path: "/taxonomy", icon: Database },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="fixed left-0 top-0 h-full w-72 bg-slate-950 text-white flex flex-col p-6 z-[60]">
      {/* Brand Section */}
      <Link to="/" className="flex items-center gap-3 mb-10 group">
        <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl overflow-hidden transition-transform group-hover:scale-105 shadow-xl">
          <img 
            src="https://image2url.com/r2/default/images/1775940968821-02d22e15-79dc-4d93-aae9-8f374238fcb4.png" 
            alt="Talentra Logo" 
            className="h-full w-full relative left-0.5 object-cover"
          />
        </div>
        <span className="font-display text-2xl font-bold tracking-tight text-white">TALENTRA</span>
      </Link>

      {/* Navigation section */}
      <div className="flex-1 space-y-2">
        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-4 ml-2">App Center</p>
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center justify-between group px-4 py-3.5 rounded-2xl transition-all ${
              isActive(item.path) 
                ? "bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/10" 
                : "text-slate-400 hover:bg-slate-900 hover:text-white"
            }`}
          >
            <div className="flex items-center gap-3">
              <item.icon size={20} />
              <span className="font-bold text-sm tracking-wide">{item.label}</span>
            </div>
            {isActive(item.path) && <ChevronRight size={16} />}
          </Link>
        ))}
      </div>

      {/* Bottom Section: Profile & Auth */}
      <div className="mt-auto pt-8 border-t border-slate-900">
        {isLoggedIn ? (
          <div className="space-y-4">
             <Link 
              to="/profile"
              className={`flex items-center gap-4 p-3 rounded-2xl transition-all ${
                isActive("/profile") ? "bg-slate-900 ring-1 ring-slate-800" : "hover:bg-slate-900"
              }`}
            >
              <div className="h-10 w-10 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-700 overflow-hidden">
                {user.photo ? (
                  <img src={user.photo} alt="Profile" className="h-full w-full object-cover" />
                ) : (
                  <span className="text-xs font-bold text-emerald-400">{user.initials}</span>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold truncate">{user.name}</p>
                <p className="text-[10px] text-slate-500 font-bold uppercase truncate">Intelligence Lead</p>
              </div>
            </Link>

            <button
              onClick={onLogout}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-slate-500 hover:text-red-400 hover:bg-red-400/5 transition-all group"
            >
              <LogOut size={18} className="group-hover:rotate-12 transition-transform" />
              <span className="text-sm font-bold">Sign Out</span>
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <button
              onClick={() => onOpenAuth("login")}
              className="w-full flex items-center justify-center gap-3 rounded-2xl border border-slate-800 py-3 text-sm font-bold text-slate-300 transition-all hover:bg-slate-900 active:scale-[0.98]"
            >
              <LogIn size={18} />
              Log In
            </button>
            <button
              onClick={() => onOpenAuth("signup")}
              className="w-full flex items-center justify-center gap-3 rounded-2xl bg-emerald-500 py-3 text-sm font-bold text-slate-950 transition-all hover:bg-emerald-400 active:scale-[0.98] shadow-lg shadow-emerald-500/10"
            >
              <UserPlus size={18} />
              Get Started
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
