import { Link, Route, Routes } from "react-router-dom";
import ProjectsList from "./pages/ProjectsList";
import ProjectPage from "./pages/ProjectPage";
import CompareVariants from "./pages/CompareVariants";
import FeedbackForm from "./pages/FeedbackForm";
import { StateScreen } from "./components/StateScreen";

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-line bg-card">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-2 flex items-center">
          <Link to="/" className="inline-flex min-h-[44px] items-center font-semibold text-ink">
            Pflanzer Method <span className="mx-2 text-muted" aria-hidden="true">|</span>
            <span className="font-normal text-muted">pflanzer.cz/method</span>
          </Link>
        </div>
      </header>
      <main className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 py-6 sm:py-8">
        <Routes>
          <Route path="/" element={<ProjectsList />} />
          <Route path=":slug" element={<ProjectPage />} />
          <Route path=":slug/compare" element={<CompareVariants />} />
          <Route path=":slug/feedback/:variantId" element={<FeedbackForm />} />
          <Route path="*" element={
            <StateScreen title="Stránka nenalezena">Zkontrolujte odkaz, který jste dostali.</StateScreen>} />
        </Routes>
      </main>
      <footer className="border-t border-line bg-card">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-3 text-sm text-muted">
          Náhledy jsou zkušební verze, ne ostrý provoz.
        </div>
      </footer>
    </div>
  );
}
