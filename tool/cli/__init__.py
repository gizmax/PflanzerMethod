"""Pflanzer tool CLI — orchestration backend for Claude Code slash commands.

Modules:
    db          — SQLite helpers (connection, audit logging, prompt logging).
    charter     — Kickoff: Charter logic + persist.
    roles       — roles: Role decision tree + 3-mode AI/human matrix.
    triage      — triage: 4 parallel triage tracks aggregation.
    builder_decision — Build: vibe-coding builder choice per stack.
    session     — Build orchestrator helpers.
    feedback_pull — Async: web hub feedback ingestion + DDD audit.
    session_2   — Rozhodnutí: conflict resolution + Decider call.
    conflict_resolver — Rozhodnutí: hierarchie závaznosti aplikuje.
    handoff     — Handoff: handoff package generator.
    method_metrics — Handoff: method-level metrics tracking.
"""

__version__ = "0.1.0"
