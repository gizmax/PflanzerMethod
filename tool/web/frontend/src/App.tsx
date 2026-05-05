import { Link, Route, Routes } from "react-router-dom";
import ProjectsList from "./pages/ProjectsList";
import ProjectPage from "./pages/ProjectPage";
import CompareVariants from "./pages/CompareVariants";
import FeedbackForm from "./pages/FeedbackForm";

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-brand-50 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="font-semibold text-brand-900 hover:text-brand-700">
            Pflanzer · Method Hub
          </Link>
          <span className="text-xs text-brand-500 font-mono">v0.1 · noindex</span>
        </div>
      </header>
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
        <Routes>
          <Route path="/" element={<ProjectsList />} />
          <Route path=":slug" element={<ProjectPage />} />
          <Route path=":slug/compare" element={<CompareVariants />} />
          <Route path=":slug/feedback/:variantId" element={<FeedbackForm />} />
        </Routes>
      </main>
      <footer className="border-t border-brand-50 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-3 text-xs text-brand-500 font-mono">
          Hybrid form-factor (ADR-0008) · Sandbox watermark · 24h TTL prototypes · noindex.
        </div>
      </footer>
    </div>
  );
}
