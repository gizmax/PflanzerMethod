import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link, Route, Routes } from "react-router-dom";
import ProjectsList from "./pages/ProjectsList";
import ProjectPage from "./pages/ProjectPage";
import CompareVariants from "./pages/CompareVariants";
import FeedbackForm from "./pages/FeedbackForm";
export default function App() {
    return (_jsxs("div", { className: "min-h-screen flex flex-col", children: [_jsx("header", { className: "border-b border-brand-50 bg-white", children: _jsxs("div", { className: "max-w-6xl mx-auto px-6 py-4 flex items-center justify-between", children: [_jsx(Link, { to: "/", className: "font-semibold text-brand-900 hover:text-brand-700", children: "Pflanzer \u00B7 Method Hub" }), _jsx("span", { className: "text-xs text-brand-500 font-mono", children: "v0.1 \u00B7 noindex" })] }) }), _jsx("main", { className: "flex-1 max-w-6xl mx-auto w-full px-6 py-8", children: _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(ProjectsList, {}) }), _jsx(Route, { path: ":slug", element: _jsx(ProjectPage, {}) }), _jsx(Route, { path: ":slug/compare", element: _jsx(CompareVariants, {}) }), _jsx(Route, { path: ":slug/feedback/:variantId", element: _jsx(FeedbackForm, {}) })] }) }), _jsx("footer", { className: "border-t border-brand-50 bg-white", children: _jsx("div", { className: "max-w-6xl mx-auto px-6 py-3 text-xs text-brand-500 font-mono", children: "Hybrid form-factor (ADR-0008) \u00B7 Sandbox watermark \u00B7 24h TTL prototypes \u00B7 noindex." }) })] }));
}
