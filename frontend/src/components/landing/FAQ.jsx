import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Minus } from "lucide-react";

const faqs = [
  {
    question: "How accurate is the resume parsing?",
    answer: "Talentra uses state-of-the-art LLMs (Claude 3.5 & GPT-4o) combined with proprietary extraction logic to achieve 99% accuracy on standard formats and significantly higher accuracy on complex layouts compared to legacy parsers."
  },
  {
    question: "Do you support PDF and scanned documents?",
    answer: "Yes, we support PDF, DOCX, and common text formats. Our ingestion layer includes OCR capabilities for high-quality scanned documents to ensure no candidate data is missed."
  },
  {
    question: "How does the skill taxonomy mapping work?",
    answer: "We map extracted skills to a standardized, hierarchical taxonomy. This ensures that variations like 'React JS' and 'React.js' are treated as the same skill, allowing for consistent matching across your entire database."
  },
  {
    question: "Can I self-host the Talentra data store?",
    answer: "Our Enterprise plan supports on-premise and VPC deployments for organizations with strict data residency requirements. Contact our sales team for more details."
  }
];

function FAQItem({ faq }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border-b border-slate-200">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between py-6 text-left focus:outline-none"
      >
        <span className="text-lg font-bold text-slate-900">{faq.question}</span>
        <div className={`flex h-8 w-8 items-center justify-center rounded-full transition-all ${isOpen ? 'bg-slate-900 text-white rotate-180' : 'bg-slate-100 text-slate-500'}`}>
          {isOpen ? <Minus size={16} /> : <Plus size={16} />}
        </div>
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <p className="pb-6 text-slate-600 leading-relaxed">
              {faq.answer}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function FAQ() {
  return (
    <div className="py-24 bg-white">
      <div className="mx-auto max-w-4xl px-6">
        <div className="text-center mb-16">
          <h2 className="text-base font-bold leading-7 text-emerald-600 uppercase tracking-widest">Support</h2>
          <p className="mt-2 font-display text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Questions? <span className="text-slate-400">We have answers.</span>
          </p>
        </div>
        
        <div className="mt-10 space-y-2">
          {faqs.map((faq) => (
            <FAQItem key={faq.question} faq={faq} />
          ))}
        </div>
      </div>
    </div>
  );
}
