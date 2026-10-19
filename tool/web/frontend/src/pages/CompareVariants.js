import { jsxs as _jsxs, jsx as _jsx } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
export default function CompareVariants() {
    const { slug } = useParams();
    const [variants, setVariants] = useState([]);
    const [error, setError] = useState(null);
    useEffect(() => {
        if (!slug)
            return;
        api.listVariants(slug).then(setVariants).catch((e) => setError(String(e)));
    }, [slug]);
    if (error)
        return _jsxs("div", { className: "pf-card text-severity-critical", children: ["Chyba: ", error] });
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsxs("h1", { children: ["Variants \u2014 ", slug] }), _jsx(Link, { to: `/${slug}`, className: "pf-button-secondary", children: "\u2190 Zp\u011Bt na projekt" })] }), variants.length === 0 ? (_jsx("div", { className: "pf-card", children: _jsxs("p", { className: "text-brand-500", children: ["\u017D\u00E1dn\u00E9 variants zat\u00EDm nebyly publikov\u00E1ny. V Claude Code:", " ", _jsxs("code", { className: "font-mono bg-brand-50 px-1.5 py-0.5 rounded", children: ["/pflanzer-session-1 ", slug] })] }) })) : (_jsx("div", { className: "grid gap-4 md:grid-cols-2 lg:grid-cols-3", children: variants.map((v) => (_jsxs("article", { className: "pf-card flex flex-col", children: [_jsxs("div", { className: "flex items-start justify-between mb-2", children: [_jsxs("h2", { children: ["Varianta ", v.name] }), _jsx("span", { className: "text-xs font-mono bg-brand-50 px-2 py-0.5 rounded", children: v.builder })] }), v.description_md && (_jsx("p", { className: "text-sm text-brand-700 mb-3 line-clamp-4", children: v.description_md })), v.preference_score !== null && (_jsxs("div", { className: "text-xs text-brand-500 mb-3", children: ["Preference score: ", _jsx("strong", { children: (v.preference_score ?? 0).toFixed(2) })] })), _jsx("div", { className: "aspect-video bg-brand-50 rounded mb-3 overflow-hidden", children: _jsx("iframe", { src: v.prototype_url, title: `Variant ${v.name}`, className: "w-full h-full", sandbox: "allow-scripts allow-same-origin allow-forms", loading: "lazy" }) }), _jsxs("div", { className: "mt-auto flex gap-2", children: [_jsx("a", { href: v.prototype_url, target: "_blank", rel: "noopener noreferrer", className: "pf-button-secondary flex-1 text-center", children: "Otev\u0159\u00EDt v nov\u00E9m okn\u011B" }), _jsx(Link, { to: `/${slug}/feedback/${v.id}`, className: "pf-button flex-1 text-center", children: "D\u00E1t feedback" })] })] }, v.id))) }))] }));
}
