import { motion } from "framer-motion";
import { Quote } from "lucide-react";

const testimonials = [
  {
    content: "Talentra's ability to map our messy resume data into a clean, hierarchical skill taxonomy changed everything. We've cut screening time by 60%.",
    author: "Elena Rodriguez",
    role: "Head of Talent, Nexus AI",
    avatar: "ER"
  },
  {
    content: "The semantic matching is frighteningly accurate. It found candidates our previous Boolean searches completely missed.",
    author: "Marcus Chen",
    role: "Lead Recruiter, CloudScale",
    avatar: "MC"
  },
  {
    content: "Building an intake center with Talentra was the best tech decision this year. The API is robust and the extraction is flawless.",
    author: "David Varkey",
    role: "CTO, TalentStream",
    avatar: "DV"
  }
];

export default function Testimonials() {
  return (
    <div className="py-24 sm:py-32 overflow-hidden">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center mb-16">
          <h2 className="text-base font-bold leading-7 text-emerald-600 uppercase tracking-widest">Impact</h2>
          <p className="mt-2 font-display text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Trusted by teams <span className="text-slate-400">redefining recruitment.</span>
          </p>
        </div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {testimonials.map((testimonial, index) => (
            <motion.div
              key={testimonial.author}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="relative rounded-3xl bg-white p-8 shadow-xl shadow-slate-200/50 border border-slate-100 transition-transform hover:-translate-y-2"
            >
              <div className="absolute -top-4 -right-4 h-12 w-12 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
                <Quote size={20} />
              </div>
              <p className="text-lg leading-relaxed text-slate-700 mb-8 italic">
                "{testimonial.content}"
              </p>
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-slate-950 flex items-center justify-center text-emerald-400 font-bold">
                  {testimonial.avatar}
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900">{testimonial.author}</h4>
                  <p className="text-xs text-slate-500">{testimonial.role}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
