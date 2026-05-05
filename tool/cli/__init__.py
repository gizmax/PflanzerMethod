"""Pflanzer tool CLI — orchestration backend for Claude Code slash commands.

Modules:
    db          — SQLite helpers (connection, audit logging, prompt logging).
    charter     — Slice 1: Charter wizard logic + persist.
    roles       — Slice 2: Role decision tree + 3-mode AI/human matrix.
    triage      — Slice 3: 4 parallel triage tracks aggregation.
    builder_decision — Slice 5: vibe-coding builder choice per stack.
    session     — Slice 5: Session 1 orchestrator helpers.
    feedback_pull — Slice 6: web hub feedback ingestion + DDD audit.
    session_2   — Slice 7: Session 2 conflict resolution + Decider call.
    conflict_resolver — Slice 7: hierarchie závaznosti aplikuje.
    handoff     — Slice 8: handoff package generator.
    method_metrics — Slice 8: method-level metrics tracking.
"""

__version__ = "0.1.0"
