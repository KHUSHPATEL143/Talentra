import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import Hero from "../components/landing/Hero";
import Features from "../components/landing/Features";
import Testimonials from "../components/landing/Testimonials";
import Process from "../components/landing/Process";
import Pricing from "../components/landing/Pricing";
import FAQ from "../components/landing/FAQ";
import Footer from "../components/Footer";

export default function LandingPage() {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate("/intake");
  };

  return (
    <div className="overflow-x-hidden">
      <Hero onGetStarted={handleGetStarted} />
      
      <div className="pt-20">
        <Features />
      </div>

      <Testimonials />

      <Process onGetStarted={handleGetStarted} />

      <Pricing />

      <FAQ />

      <section className="py-24 bg-slate-950 text-white mx-6 rounded-[3rem] my-20 relative overflow-hidden">
        <div className="absolute top-0 right-0 -translate-y-1/2 translate-x-1/2 h-96 w-96 rounded-full bg-emerald-500/20 blur-3xl" />
        <div className="absolute bottom-0 left-0 translate-y-1/2 -translate-x-1/2 h-96 w-96 rounded-full bg-sky-500/20 blur-3xl" />
        
        <div className="mx-auto max-w-4xl px-6 text-center relative z-10">
          <motion.h2 
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="font-display text-4xl font-bold tracking-tight sm:text-5xl"
          >
            Ready to unlock the intelligence <br />
            <span className="text-emerald-400">hidden in your resumes?</span>
          </motion.h2>
          <p className="mt-6 text-lg text-slate-300">
            Join 500+ recruitment teams using Talentra to accelerate their talent mapping.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={handleGetStarted}
              className="w-full sm:w-auto rounded-full bg-white px-8 py-4 text-sm font-bold text-slate-950 transition-all hover:bg-emerald-50 hover:scale-105 active:scale-95"
            >
              Get Started for Free
            </button>
            <button className="w-full sm:w-auto rounded-full bg-white/10 px-8 py-4 text-sm font-bold text-white border border-white/20 transition-all hover:bg-white/20">
              Schedule a Demo
            </button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
