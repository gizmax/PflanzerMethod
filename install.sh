#!/usr/bin/env bash
# Pflanzer Method — installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/pflanzer-method/PflanzerMethod/main/install.sh | bash
#   nebo:
#   bash install.sh                 # z lokálního cloneu
#   PFLANZER_REF=v1.0 bash install.sh   # specific version
#
# Co dělá:
# 1. Ověří dependencies (git, python3.10+, node 20+)
# 2. Naclonuje Pflanzer repo do ~/.claude/plugins/pflanzer/
# 3. Apply DB schema do ~/.pflanzer/pflanzer.db
# 4. Vytvoří ~/.pflanzer/ runtime dir (targets/, handoffs/, charters/)
# 5. Print next-step instrukce

set -euo pipefail

PFLANZER_REPO="${PFLANZER_REPO:-https://github.com/pflanzer-method/PflanzerMethod.git}"
PFLANZER_REF="${PFLANZER_REF:-main}"
PLUGIN_DIR="${HOME}/.claude/plugins/pflanzer"
RUNTIME_DIR="${HOME}/.pflanzer"

# Colors (no-op if non-TTY)
if [ -t 1 ]; then
  C_BOLD=$'\033[1m'; C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_ERR=$'\033[31m'; C_RST=$'\033[0m'
else
  C_BOLD=''; C_OK=''; C_WARN=''; C_ERR=''; C_RST=''
fi

step() { echo "${C_BOLD}==>${C_RST} $1"; }
ok()   { echo "  ${C_OK}✓${C_RST} $1"; }
warn() { echo "  ${C_WARN}⚠${C_RST} $1"; }
fail() { echo "  ${C_ERR}✗${C_RST} $1" >&2; exit 1; }

# ---------------------------------------------------------------------------
# 1. Dependency check
# ---------------------------------------------------------------------------
step "Kontroluji dependencies"

command -v git >/dev/null   || fail "git není v PATH"
command -v python3 >/dev/null || fail "python3 není v PATH (potřebuju 3.10+)"
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
  fail "Python ${PY_VER} je < 3.10. Upgrade prosím."
fi
ok "git, python3 ${PY_VER}"

if command -v node >/dev/null; then
  NODE_VER=$(node --version | sed 's/^v//')
  ok "node ${NODE_VER} (potřebuju 20.11+ pro skeleton; jen runtime)"
else
  warn "node není v PATH — nutný pro 'npm run dev' v extracted sessions"
fi

if command -v claude >/dev/null; then
  ok "claude (Claude Code) v PATH"
else
  warn "claude (Claude Code CLI) není v PATH — Pflanzer slash commands fungují jen uvnitř claude"
fi

# ---------------------------------------------------------------------------
# 2. Plugin clone do ~/.claude/plugins/pflanzer/
# ---------------------------------------------------------------------------
step "Instaluji plugin do ${PLUGIN_DIR}"

mkdir -p "$(dirname "$PLUGIN_DIR")"
if [ -d "$PLUGIN_DIR/.git" ]; then
  ok "Plugin už existuje, fetch + checkout ${PFLANZER_REF}"
  git -C "$PLUGIN_DIR" fetch --quiet origin
  git -C "$PLUGIN_DIR" checkout --quiet "$PFLANZER_REF"
  git -C "$PLUGIN_DIR" pull --quiet --ff-only || warn "fast-forward not possible (local commits?)"
else
  if [ -d "$PLUGIN_DIR" ] && [ "$(ls -A "$PLUGIN_DIR")" ]; then
    fail "${PLUGIN_DIR} existuje a není prázdný — odstraň ho ručně"
  fi
  rmdir "$PLUGIN_DIR" 2>/dev/null || true
  git clone --quiet --depth 1 --branch "$PFLANZER_REF" "$PFLANZER_REPO" "$PLUGIN_DIR"
  ok "Naclonováno z ${PFLANZER_REPO} (ref ${PFLANZER_REF})"
fi

# ---------------------------------------------------------------------------
# 3. Runtime dir + DB schema
# ---------------------------------------------------------------------------
step "Setup runtime dir ${RUNTIME_DIR}"

mkdir -p "$RUNTIME_DIR"/{targets,handoffs,charters,sessions,feedback,quick,production_reports}
ok "Vytvořeny pod-adresáře (targets, handoffs, charters, sessions, ...)"

# Apply DB migration (idempotent)
if PYTHONPATH="$PLUGIN_DIR" python3 "$PLUGIN_DIR/tool/db/migrate.py"; then
  ok "DB schema aplikováno: ${RUNTIME_DIR}/pflanzer.db"
else
  fail "Migration selhalo — zkontroluj ${PLUGIN_DIR}/tool/db/schema.sql"
fi

# ---------------------------------------------------------------------------
# 4. Symlinky pro PATH access (volitelné)
# ---------------------------------------------------------------------------
step "Setup PATH wrapper"

WRAPPER="${HOME}/.local/bin/pflanzer"
mkdir -p "$(dirname "$WRAPPER")"
cat > "$WRAPPER" <<'EOF'
#!/usr/bin/env bash
# Pflanzer CLI wrapper — proxies subcommands na tool/cli/<name>.py
PLUGIN_DIR="${PFLANZER_PLUGIN_DIR:-$HOME/.claude/plugins/pflanzer}"
SUB="${1:-help}"
shift || true
SCRIPT="${PLUGIN_DIR}/tool/cli/${SUB}.py"
if [ ! -f "$SCRIPT" ]; then
  echo "Unknown subcommand: $SUB"
  echo "Available:"
  ls "${PLUGIN_DIR}/tool/cli/"*.py | xargs -n1 basename | sed 's/.py$//' | grep -v '^__' | sed 's/^/  pflanzer /'
  exit 1
fi
PYTHONPATH="$PLUGIN_DIR" exec python3 "$SCRIPT" "$@"
EOF
chmod +x "$WRAPPER"
ok "Wrapper script: ${WRAPPER}"

case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) warn "${HOME}/.local/bin není v PATH — přidej do ~/.zshrc nebo ~/.bashrc:"
     echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
     ;;
esac

# ---------------------------------------------------------------------------
# 5. Done — next steps
# ---------------------------------------------------------------------------
echo ""
echo "${C_OK}${C_BOLD}✅ Pflanzer Method nainstalována.${C_RST}"
echo ""
echo "Co dál:"
echo ""
echo "  ${C_BOLD}1.${C_RST} V Claude Code v jakémkoliv repu spusť slash command:"
echo "       /pflanzer \"co dnes řešíme\""
echo ""
echo "  ${C_BOLD}2.${C_RST} Před první session na produkčním repu vyrob INTEGRATION_GUIDE.md:"
echo "       cd /path/to/your/repo"
echo "       pflanzer init   # zkopíruje template + ověří env"
echo ""
echo "  ${C_BOLD}3.${C_RST} Dokumentace metody:"
echo "       ${PLUGIN_DIR}/README.md"
echo "       ${PLUGIN_DIR}/docs/methodology/00-tldr.md"
echo ""
echo "  ${C_BOLD}4.${C_RST} Update na novou verzi:"
echo "       pflanzer update      # = git pull v ${PLUGIN_DIR}"
echo ""
echo "  ${C_BOLD}5.${C_RST} Uninstall:"
echo "       rm -rf ${PLUGIN_DIR} ${RUNTIME_DIR} ${WRAPPER}"
echo ""
