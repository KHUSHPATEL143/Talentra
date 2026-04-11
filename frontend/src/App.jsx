import { useState } from "react";
import { Link, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import Intake from "./pages/Intake";
import CandidateProfile from "./pages/CandidateProfile";
import MatchPage from "./pages/MatchPage";
import TaxonomyPage from "./pages/TaxonomyPage";
import Profile from "./pages/Profile";
import Sidebar from "./components/Sidebar";
import AuthModal from "./components/AuthModal";
import { getClientApiKey, setClientApiKey } from "./services/api";
import { Cpu } from "lucide-react";

export default function App() {
  const [apiKey, setApiKey] = useState(getClientApiKey());
  
  // Persist auth state and user data
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    return localStorage.getItem("talentra_isLoggedIn") === "true";
  });
  
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("talentra_user");
    if (savedUser) {
      const parsed = JSON.parse(savedUser);
      // Clean up session-specific blob URLs that can't be persisted
      if (parsed.photo && parsed.photo.startsWith("blob:")) {
        delete parsed.photo;
      }
      return parsed;
    }
    return { name: "Jan Doe", email: "", initials: "JD" };
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
    <div className="flex min-h-screen bg-slate-50 font-body selection:bg-emerald-100 selection:text-emerald-900 overflow-x-hidden">
      <AuthModal 
        isOpen={authModal.isOpen} 
        onClose={closeAuth} 
        type={authModal.type} 
        onSuccess={handleAuthSuccess}
      />

      {/* Sidebar - Visible on all pages except for landing page when logged out */}
      {(!isLandingPage || isLoggedIn) && (
        <Sidebar 
          isLoggedIn={isLoggedIn} 
          user={user} 
          onLogout={handleLogout} 
          onOpenAuth={openAuth} 
        />
      )}

      {/* Top Header Placeholder for Landing Page - Only when logged out */}
      {isLandingPage && !isLoggedIn && (
        <header className="absolute top-0 right-0 left-0 z-50 flex items-center justify-between px-10 py-6 bg-transparent">
          <Link to="/" className="flex items-center gap-3 font-display text-2xl font-bold tracking-tight text-slate-950 group">
            <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl overflow-hidden transition-transform group-hover:scale-105 shadow-xl shadow-slate-950/10">
              <img 
                src="https://image2url.com/r2/default/images/1775940968821-02d22e15-79dc-4d93-aae9-8f374238fcb4.png" 
                alt="Talentra Logo" 
                className="h-full w-full object-cover"
              />
            </div>
            <span>TALENTRA</span>
          </Link>
          <div className="flex gap-4">
            <button onClick={() => openAuth("login")} className="px-6 py-2.5 text-sm font-bold text-slate-800 hover:text-emerald-600 transition-colors">Log In</button>
            <button onClick={() => openAuth("signup")} className="px-8 py-2.5 rounded-full bg-slate-950 text-white text-sm font-bold shadow-xl shadow-slate-950/10 hover:bg-slate-800 transition-all">Get Started</button>
          </div>
        </header>
      )}

      <main className={`flex-1 transition-all duration-300 ${(!isLandingPage || isLoggedIn) ? "ml-72" : ""}`}>
        <div className={`mx-auto max-w-7xl px-8 ${isLandingPage ? "py-0" : "py-10"}`}>
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
        </div>
      </main>
    </div>
  );
}


