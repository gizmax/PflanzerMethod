import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
export default function ProjectsList() {
    const [projects, setProjects] = useState([]);
    const [error, setError] = useState(null);
    useEffect(() => {
        api.listProjects().then(setProjects).catch((e) => setError(String(e)));
    }, []);
    if (error)
        return _jsxs("div", { className: "pf-card text-severity-critical", children: ["Chyba: ", error] });
    if (!projects.length) {
        return (_jsxs("div", { className: "pf-card", children: [_jsx("h1", { children: "Pflanzer projekty" }), _jsxs("p", { className: "mt-2 text-brand-500", children: ["\u017D\u00E1dn\u00E9 projekty zat\u00EDm nejsou. Spus\u0165 v Claude Code:", " ", _jsx("code", { className: "font-mono bg-brand-50 px-1.5 py-0.5 rounded", children: "/pflanzer-charter <slug>" })] })] }));
    }
    return (_jsxs("div", { className: "space-y-4", children: [_jsxs("h1", { children: ["Pflanzer projekty (", projects.length, ")"] }), _jsx("div", { className: "grid gap-3 md:grid-cols-2", children: projects.map((p) => (_jsxs(Link, { to: `/${p.slug}`, className: "pf-card hover:border-brand-700 block", children: [_jsxs("div", { className: "flex items-start justify-between mb-2", children: [_jsx("h2", { className: "text-base", children: p.name }), _jsx("span", { className: "text-xs font-mono px-2 py-0.5 bg-brand-50 rounded", children: p.status })] }), _jsx("p", { className: "text-xs font-mono text-brand-500 mb-2", children: p.slug }), p.xyz_hypothesis && (_jsx("p", { className: "text-sm text-brand-700 line-clamp-3", children: p.xyz_hypothesis }))] }, p.id))) })] }));
}
