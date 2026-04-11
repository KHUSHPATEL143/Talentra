import { Link } from "react-router-dom";
import { Cpu, Code, Send, Briefcase, Mail } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-white border-t border-slate-200 pt-24 pb-12">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-4 lg:gap-8">
          <div className="lg:col-span-1">
            <Link to="/" className="flex items-center gap-2.5 font-display text-2xl font-bold tracking-tight text-slate-950">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-emerald-400">
                <Cpu size={24} />
              </div>
              <span>GARUDA</span>
            </Link>
            <p className="mt-6 text-sm leading-7 text-slate-600 max-w-xs">
              Pioneering the next generation of resume intelligence and talent mapping with high-order LLMs.
            </p>
            <div className="mt-8 flex gap-5">
              <a href="#" className="text-slate-400 hover:text-emerald-600 transition-colors">
                <Code size={20} />
              </a>
              <a href="#" className="text-slate-400 hover:text-emerald-600 transition-colors">
                <Send size={20} />
              </a>
              <a href="#" className="text-slate-400 hover:text-emerald-600 transition-colors">
                <Briefcase size={20} />
              </a>
              <a href="#" className="text-slate-400 hover:text-emerald-600 transition-colors">
                <Mail size={20} />
              </a>
            </div>
          </div>
          
          <div>
            <h3 className="text-sm font-bold uppercase tracking-widest text-slate-900">Platform</h3>
            <ul className="mt-6 space-y-4">
              <li><Link to="/intake" className="text-sm text-slate-600 hover:text-emerald-600 transition-colors">Resume Intake</Link></li>
              <li><Link to="/match" className="text-sm text-slate-600 hover:text-emerald-600 transition-colors">Precision Matching</Link></li>
              <li><Link to="/taxonomy" className="text-sm text-slate-600 hover:text-emerald-600 transition-colors">Skill Taxonomy</Link></li>
              <li><a href="#" className="text-sm text-slate-600 hover:text-emerald-600 transition-colors">API Reference</a></li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-sm font-bold uppercase tracking-widest text-slate-900">Company</h3>
            <ul className="mt-6 space-y-4">
              <li><a href="#" className="text-sm text-slate-600 hover:text-emerald-600 transition-colors">About Us</a></li>
              <li><a href="#" className="text-sm text-slate-600 hover:text-emerald-600 transition-colors">Careers</a></li>
              <li><a href="#" className="text-sm text-slate-600 hover:text-emerald-600 transition-colors">Legal</a></li>
              <li><a href="#" className="text-sm text-slate-600 hover:text-emerald-600 transition-colors">Privacy Policy</a></li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-sm font-bold uppercase tracking-widest text-slate-900">Newsletter</h3>
            <p className="mt-6 text-sm leading-7 text-slate-600">
              Get the latest updates on AI in recruitment delivered to your inbox.
            </p>
            <form className="mt-6 flex max-w-md gap-x-4">
              <input
                id="email-address"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="min-w-0 flex-auto rounded-full border border-slate-300 bg-white px-4 py-2 text-slate-950 shadow-sm focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 text-sm outline-none"
                placeholder="Enter your email"
              />
              <button
                type="submit"
                className="flex-none rounded-full bg-slate-950 px-5 py-2 text-sm font-bold text-white shadow-sm hover:bg-slate-800 transition-all active:scale-95"
              >
                Join
              </button>
            </form>
          </div>
        </div>
        
        <div className="mt-20 border-t border-slate-100 pt-8 text-center sm:flex sm:items-center sm:justify-between">
          <p className="text-xs leading-5 text-slate-400">
            &copy; {new Date().getFullYear()} Garuda Intelligence Inc. Built for the Hackathon-3.
          </p>
        </div>
      </div>
    </footer>
  );
}
