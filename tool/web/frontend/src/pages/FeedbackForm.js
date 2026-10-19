import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
const SEVERITIES = ["critical", "high", "medium", "low"];
const WCAG = ["N/A", "A", "AA", "AAA"];
// 6 kroků cesty (ADR-0021) — fallback, když zástupce není v role catalogu
const PATH_STEPS = ["Byznys", "Produkt", "Design", "Vývoj", "Bezpečnost & právo", "Provoz"];
export default function FeedbackForm() {
    const { slug, variantId } = useParams();
    const navigate = useNavigate();
    const [variant, setVariant] = useState(null);
    const [roles, setRoles] = useState([]);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);
    // Form state
    const [roleId, setRoleId] = useState(null);
    const [severity, setSeverity] = useState("medium");
    const [department, setDepartment] = useState("");
    const [category, setCategory] = useState("");
    const [score, setScore] = useState(0.7);
    const [rationale, setRationale] = useState("");
    const [aiActDim, setAiActDim] = useState("");
    const [wcagLevel, setWcagLevel] = useState("N/A");
    const [isAiOnly, setIsAiOnly] = useState(false);
    useEffect(() => {
        if (!slug || !variantId)
            return;
        Promise.all([api.listVariants(slug), api.getProject(slug)])
            .then(([vs, detail]) => {
            const v = vs.find((x) => x.id === Number(variantId));
            setVariant(v ?? null);
            setRoles(detail.roles);
        })
            .catch((e) => setError(String(e)));
    }, [slug, variantId]);
    async function onSubmit(e) {
        e.preventDefault();
        if (!variant)
            return;
        if (!rationale.trim()) {
            setError("Rationale je povinné (per metodika v0.2.1).");
            return;
        }
        setSubmitting(true);
        setError(null);
        try {
            const role = roles.find((r) => r.id === roleId);
            const dept = role?.catalog_label || department || "unknown";
            await api.submitFeedback({
                variant_id: variant.id,
                role_id: roleId,
                severity,
                department: dept,
                category: category || "general",
                score,
                rationale,
                ai_act_dimension: aiActDim || null,
                wcag_level: wcagLevel,
                is_ai_only: isAiOnly,
            });
            setSuccess(true);
            setTimeout(() => navigate(`/${slug}/compare`), 1500);
        }
        catch (e) {
            setError(String(e));
        }
        finally {
            setSubmitting(false);
        }
    }
    if (!variant)
        return _jsx("div", { className: "pf-card", children: "Na\u010D\u00EDt\u00E1m\u2026" });
    // Score deflation warning (devil's advocate Útok 6 — heuristic, not measurement)
    const deflatedScore = isAiOnly && score > 0.5 ? 0.5 : score;
    return (_jsxs("div", { className: "space-y-4", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsxs("h1", { children: ["Feedback \u2014 Varianta ", variant.name] }), _jsx(Link, { to: `/${slug}/compare`, className: "pf-button-secondary", children: "\u2190 Zp\u011Bt" })] }), _jsxs("form", { onSubmit: onSubmit, className: "pf-card space-y-4 max-w-2xl", children: [_jsxs("div", { children: [_jsx("label", { className: "pf-label", children: "Role (z role catalogu projektu)" }), _jsxs("select", { className: "pf-input", value: roleId ?? "", onChange: (e) => setRoleId(e.target.value ? Number(e.target.value) : null), children: [_jsx("option", { value: "", children: "\u2014 vyber roli \u2014" }), roles.map((r) => (_jsxs("option", { value: r.id, children: ["#", r.catalog_idx, " ", r.catalog_label, " (", r.ai_proxy_mode, ")"] }, r.id)))] }), roleId === null && (_jsxs("select", { className: "pf-input mt-2", value: department, onChange: (e) => setDepartment(e.target.value), children: [_jsx("option", { value: "", children: "\u2014 nebo krok cesty \u2014" }), PATH_STEPS.map((step) => (_jsx("option", { value: step, children: step }, step)))] }))] }), _jsxs("div", { className: "grid grid-cols-2 gap-3", children: [_jsxs("div", { children: [_jsx("label", { className: "pf-label", children: "Severity" }), _jsx("select", { className: "pf-input", value: severity, onChange: (e) => setSeverity(e.target.value), children: SEVERITIES.map((s) => (_jsx("option", { value: s, children: s }, s))) })] }), _jsxs("div", { children: [_jsx("label", { className: "pf-label", children: "Kategorie" }), _jsx("input", { className: "pf-input", value: category, onChange: (e) => setCategory(e.target.value), placeholder: "nap\u0159. ux, tech, security, legal, a11y" })] })] }), _jsxs("div", { children: [_jsxs("label", { className: "pf-label", children: ["Score z\u00E1vaznosti: ", _jsx("strong", { children: deflatedScore.toFixed(2) }), isAiOnly && score > 0.5 && (_jsxs("span", { className: "text-severity-high text-xs ml-2", children: ["(deflated z ", score.toFixed(2), " kv\u016Fli AI-only)"] }))] }), _jsx("input", { type: "range", min: 0, max: 1, step: 0.05, value: score, onChange: (e) => setScore(Number(e.target.value)), className: "w-full" })] }), _jsxs("div", { children: [_jsxs("label", { className: "pf-label", children: ["Rationale ", _jsx("span", { className: "text-severity-critical", children: "*" })] }), _jsx("textarea", { className: "pf-input min-h-[100px]", value: rationale, onChange: (e) => setRationale(e.target.value), placeholder: "Pro\u010D tento score? (povinn\u00E9 \u2014 bez rationale se rozhodnut\u00ED st\u00E1v\u00E1 politick\u00FDm)", required: true })] }), _jsxs("div", { className: "grid grid-cols-2 gap-3", children: [_jsxs("div", { children: [_jsx("label", { className: "pf-label", children: "AI Act dimension (voliteln\u00E9)" }), _jsx("input", { className: "pf-input", value: aiActDim, onChange: (e) => setAiActDim(e.target.value), placeholder: "nap\u0159. transparency, human oversight" })] }), _jsxs("div", { children: [_jsx("label", { className: "pf-label", children: "WCAG level (jen A11y feedback)" }), _jsx("select", { className: "pf-input", value: wcagLevel ?? "N/A", onChange: (e) => setWcagLevel(e.target.value), children: WCAG.map((w) => (_jsx("option", { value: w, children: w }, w))) })] })] }), _jsxs("label", { className: "inline-flex items-center gap-2", children: [_jsx("input", { type: "checkbox", checked: isAiOnly, onChange: (e) => setIsAiOnly(e.target.checked), className: "rounded" }), _jsx("span", { className: "text-sm", children: "AI-only feedback (bez human review) \u2014 score deflated max 0.5 (heuristic)" })] }), error && (_jsx("div", { className: "rounded border border-severity-critical/30 bg-severity-critical/10 p-3 text-sm text-severity-critical", children: error })), success && (_jsx("div", { className: "rounded border border-severity-low/30 bg-severity-low/10 p-3 text-sm text-severity-low", children: "Feedback ulo\u017Een. P\u0159esm\u011Brov\u00E1v\u00E1m\u2026" })), _jsxs("div", { className: "flex gap-2", children: [_jsx("button", { type: "submit", className: "pf-button", disabled: submitting, children: submitting ? "Odesílám…" : "Odeslat feedback" }), _jsx(Link, { to: `/${slug}/compare`, className: "pf-button-secondary", children: "Zru\u0161it" })] })] })] }));
}
