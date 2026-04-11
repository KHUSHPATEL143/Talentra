import { useState } from "react";
import { Link, Route, Routes, useLocation } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import Intake from "./pages/Intake";
import CandidateProfile from "./pages/CandidateProfile";
import MatchPage from "./pages/MatchPage";
import TaxonomyPage from "./pages/TaxonomyPage";
import Profile from "./pages/Profile";
import { getClientApiKey, setClientApiKey } from "./services/api";

import { LayoutDashboard, UserCheck, Database, Key, Trash2, Cpu, LogIn, UserPlus } from "lucide-react";

import { useNavigate } from "react-router-dom";
import AuthModal from "./components/AuthModal";

export default function App() {
  const [apiKey, setApiKey] = useState(getClientApiKey());
  
  // Persist auth state and user data
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    return localStorage.getItem("talentra_isLoggedIn") === "true";
  });
  
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("talentra_user");
    return savedUser ? JSON.parse(savedUser) : { name: "Jan Doe", email: "", initials: "JD" };
  });

  const [authModal, setAuthModal] = useState({ isOpen: false, type: "login" });
  
  const location = useLocation();
  const navigate = useNavigate();
  const isLandingPage = location.pathname === "/";

  const saveApiKey = () => {
    setClientApiKey(apiKey.trim());
    setApiKey(getClientApiKey());
  };

  const clearApiKey = () => {
    setClientApiKey("");
    setApiKey("");
  };

  const openAuth = (type) => setAuthModal({ isOpen: true, type });
  const closeAuth = () => setAuthModal({ ...authModal, isOpen: false });

  const handleAuthSuccess = (userData) => {
    setIsLoggedIn(true);
    localStorage.setItem("talentra_isLoggedIn", "true");
    
    if (userData?.name) {
      const names = userData.name.split(" ");
      const initials = names.length > 1 
        ? (names[0][0] + names[names.length - 1][0]).toUpperCase()
        : names[0].slice(0, 2).toUpperCase();
      
      const newUser = { ...userData, initials };
      setUser(newUser);
      localStorage.setItem("talentra_user", JSON.stringify(newUser));
    }
    closeAuth();
    if (isLandingPage) {
      navigate("/intake");
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    localStorage.removeItem("talentra_isLoggedIn");
    localStorage.removeItem("talentra_user");
    navigate("/");
  };

  const handleUpdateUser = (newData) => {
    setUser((prev) => {
      const updated = { ...prev, ...newData };
      if (newData.name) {
        const names = newData.name.split(" ");
        updated.initials = names.length > 1 
          ? (names[0][0] + names[names.length - 1][0]).toUpperCase()
          : names[0].slice(0, 2).toUpperCase();
      }
      localStorage.setItem("talentra_user", JSON.stringify(updated));
      return updated;
    });
  };

  return (
    <div className="min-h-screen font-body selection:bg-emerald-100 selection:text-emerald-900">
      <AuthModal 
        isOpen={authModal.isOpen} 
        onClose={closeAuth} 
        type={authModal.type} 
        onSuccess={handleAuthSuccess}
      />

      <header className="sticky top-0 z-50 border-b border-white/20 bg-white/40 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
          <Link to="/" className="flex items-center gap-2.5 font-display text-2xl font-bold tracking-tight text-slate-950 group">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-emerald-400 transition-transform group-hover:scale-110">
              <Cpu size={24} />
              <div className="absolute inset-0 animate-pulse rounded-xl bg-emerald-400/20" />
            </div>
            <span>GARUDA</span>
          </Link>
          
          <div className="flex flex-col gap-4 lg:items-end">
            <div className="flex items-center gap-6">
              {/* Main Navigation - Hidden on landing page unless "logged in" */}
              {(!isLandingPage || isLoggedIn) && (
                <nav className="flex items-center gap-1.5 rounded-full bg-slate-100/50 p-1.5 text-sm font-semibold text-slate-600 ring-1 ring-slate-200/50">
                  <Link to="/intake" className="flex items-center gap-2 rounded-full px-4 py-2 transition-all hover:bg-white hover:text-slate-900 hover:shadow-sm">
                    <LayoutDashboard size={16} />
                    Intake
                  </Link>
                  <Link to="/match" className="flex items-center gap-2 rounded-full px-4 py-2 transition-all hover:bg-white hover:text-slate-900 hover:shadow-sm">
                    <UserCheck size={16} />
                    Match
                  </Link>
                  <Link to="/taxonomy" className="flex items-center gap-2 rounded-full px-4 py-2 transition-all hover:bg-white hover:text-slate-900 hover:shadow-sm">
                    <Database size={16} />
                    Taxonomy
                  </Link>
                </nav>
              )}

              {/* Auth UI Placeholders */}
              <div className="flex items-center gap-3">
                {isLoggedIn ? (
                  <Link 
                    to="/profile"
                    className="group relative flex h-10 items-center gap-3 rounded-full bg-slate-100 pr-4 pl-1.5 transition-all hover:bg-slate-200"
                  >
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-950 text-[10px] font-bold text-emerald-400 overflow-hidden">
                      {user.photo ? (
                        <img src={user.photo} alt="Avatar" className="h-full w-full object-cover" />
                      ) : (
                        user.initials
                      )}
                    </div>
                    <span className="text-xs font-bold text-slate-600">{user.name}</span>
                  </Link>
                ) : (
                  <>
                    <button 
                      onClick={() => openAuth("login")}
                      className="inline-flex items-center gap-2 rounded-full px-5 py-2 text-sm font-bold text-slate-600 transition-all hover:bg-slate-100 active:scale-95"
                    >
                      <LogIn size={16} />
                      Log In
                    </button>
                    <button 
                      onClick={() => openAuth("signup")}
                      className="inline-flex items-center gap-2 rounded-full bg-slate-950 px-5 py-2 text-sm font-bold text-white transition-all hover:bg-slate-800 active:scale-95 shadow-lg shadow-slate-950/10"
                    >
                      <UserPlus size={16} />
                      Sign Up
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* API Key Management - Hidden for logged in users (now in Profile) */}
            {!isLoggedIn && (!isLandingPage || isLoggedIn) && (
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <div className="relative group">
                  <Key size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    value={apiKey}
                    onChange={(event) => setApiKey(event.target.value)}
                    placeholder="API Key for protected routes"
                    className="min-w-[280px] rounded-full border border-slate-200 bg-white/80 py-2.5 pl-10 pr-4 text-sm outline-none transition-all focus:border-emerald-400 focus:bg-white focus:ring-4 focus:ring-emerald-400/10"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={saveApiKey}
                    className="inline-flex items-center gap-2 rounded-full bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white transition-all hover:bg-slate-800 active:scale-95"
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={clearApiKey}
                    className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-slate-200/50 text-slate-600 transition-all hover:bg-red-50 hover:text-red-600 active:scale-95"
                    title="Clear Key"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-10">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/intake" element={<Intake />} />
          <Route path="/candidates/:candidateId" element={<CandidateProfile />} />
          <Route path="/match" element={<MatchPage />} />
          <Route path="/match/:candidateId" element={<MatchPage />} />
          <Route path="/taxonomy" element={<TaxonomyPage />} />
          <Route path="/profile" element={
            <Profile 
              user={user}
              apiKey={apiKey} 
              setApiKey={setApiKey} 
              onSaveKey={saveApiKey} 
              onClearKey={clearApiKey}
              onLogout={handleLogout}
              onUpdateUser={handleUpdateUser}
            />
          } />
        </Routes>
      </main>
    </div>
  );
}

