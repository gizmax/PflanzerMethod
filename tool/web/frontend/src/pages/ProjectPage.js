import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
export default function ProjectPage() {
    const { slug } = useParams();
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    useEffect(() => {
        if (!slug)
            return;
        api.getProject(slug).then(setData).catch((e) => setError(String(e)));
    }, [slug]);
    if (error)
        return _jsxs("div", { className: "pf-card text-severity-critical", children: ["Chyba: ", error] });
    if (!data)
        return _jsx("div", { className: "pf-card", children: "Na\u010D\u00EDt\u00E1m\u2026" });
    const { project, roles, triage } = data;
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "flex items-start justify-between", children: [_jsxs("div", { children: [_jsx("h1", { children: project.name }), _jsxs("p", { className: "text-xs font-mono text-brand-500", children: [project.slug, " \u00B7 status: ", _jsx("strong", { children: project.status })] })] }), _jsx("div", { className: "flex gap-2", children: _jsx(Link, { to: `/${slug}/compare`, className: "pf-button", children: "Compare variants" }) })] }), _jsxs("div", { className: "pf-card space-y-3", children: [_jsx("h2", { children: "Charter" }), project.xyz_hypothesis && (_jsx(Section, { label: "XYZ hypot\u00E9za", value: project.xyz_hypothesis })), _jsxs("div", { className: "grid grid-cols-2 gap-3 text-sm", children: [_jsx(KeyValue, { k: "Decider", v: project.decider_name || "—" }), _jsx(KeyValue, { k: "Sponsor", v: project.sponsor_name || "—" }), _jsx(KeyValue, { k: "AI Act tier", v: project.ai_act_tier || "—" }), _jsx(KeyValue, { k: "Data class", v: project.data_class || "—" }), _jsx(KeyValue, { k: "Throwaway / evolve", v: project.throwaway_or_evolve || "—" }), _jsx(KeyValue, { k: "Kapacita", v: `${project.capacity_profile || "—"} · ${project.capacity_person_days || 0} PD` })] }), project.primary_lagging_metric && (_jsx(Section, { label: "Primary lagging metric", value: project.primary_lagging_metric })), project.leading_metric && (_jsx(Section, { label: "Leading metric", value: project.leading_metric })), project.kill_criteria && (_jsx(Section, { label: "Kill criteria", value: project.kill_criteria }))] }), _jsxs("div", { className: "pf-card", children: [_jsxs("h2", { children: ["Role v m\u00EDstnosti (", roles.length, ")"] }), _jsxs("table", { className: "mt-3 w-full text-sm", children: [_jsx("thead", { className: "text-left text-xs text-brand-500 border-b border-brand-50", children: _jsxs("tr", { children: [_jsx("th", { className: "py-2", children: "#" }), _jsx("th", { children: "Role" }), _jsx("th", { children: "Status" }), _jsx("th", { children: "AI mode" }), _jsx("th", { children: "Owner" })] }) }), _jsx("tbody", { children: roles.map((r) => (_jsxs("tr", { className: "border-b border-brand-50/50", children: [_jsx("td", { className: "py-2 font-mono", children: r.catalog_idx }), _jsx("td", { children: r.catalog_label }), _jsx("td", { children: _jsx("span", { className: statusPill(r.status), children: r.status }) }), _jsx("td", { className: "font-mono text-xs", children: r.ai_proxy_mode }), _jsx("td", { className: "text-brand-500", children: r.human_owner || "—" })] }, r.id))) })] })] }), _jsxs("div", { className: "pf-card", children: [_jsx("h2", { children: "Pre-flight triage" }), _jsxs("div", { className: "grid gap-2 mt-3 md:grid-cols-2", children: [triage.map((t) => (_jsxs("div", { className: "border border-brand-50 rounded p-3", children: [_jsxs("div", { className: "flex items-center justify-between mb-1", children: [_jsx("span", { className: "font-medium", children: t.track }), _jsx("span", { className: statusPill(t.status), children: t.status })] }), _jsxs("p", { className: "text-xs text-brand-500", children: ["Signed by: ", t.signed_by || "—"] })] }, t.id))), triage.length === 0 && (_jsxs("p", { className: "text-brand-500 text-sm", children: ["Triage zat\u00EDm neprob\u011Bhla. V Claude Code:", " ", _jsxs("code", { className: "font-mono bg-brand-50 px-1.5 py-0.5 rounded", children: ["/pflanzer-triage ", slug] })] }))] })] })] }));
}
function Section({ label, value }) {
    return (_jsxs("div", { children: [_jsx("div", { className: "text-xs uppercase tracking-wide text-brand-500 mb-1", children: label }), _jsx("div", { className: "text-sm whitespace-pre-line", children: value })] }));
}
function KeyValue({ k, v }) {
    return (_jsxs("div", { children: [_jsx("div", { className: "text-xs text-brand-500", children: k }), _jsx("div", { className: "font-medium", children: v })] }));
}
function statusPill(status) {
    const base = "text-xs font-mono px-2 py-0.5 rounded";
    switch (status) {
        case "ok":
        case "mandatory":
        case "recommended":
            return `${base} bg-severity-low/20 text-severity-low`;
        case "blocked":
        case "killed":
            return `${base} bg-severity-critical/20 text-severity-critical`;
        case "deferred":
        case "warning":
            return `${base} bg-severity-medium/20 text-severity-high`;
        default:
            return `${base} bg-brand-50 text-brand-700`;
    }
}
