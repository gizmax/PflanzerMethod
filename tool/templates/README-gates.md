# Quality gates mimo Node/Python — `pflanzer.gates.yml`

**Adaptér.** Soubor `pflanzer.gates.yml` (bez PyYAML `pflanzer.gates.json`) v kořeni target repa říká `tool/cli/quality_gates.py`, jakým příkazem spustit který gate (`build`, `types`, `lint`, `tests`, `coverage`, `acceptance`, `security`, `a11y`, `observability`). Hledá se v kontrolovaném adresáři a v rodičích až po git root; nejbližší vyhrává. Pokud existuje, **úplně nahrazuje autodetekci**.

```yaml
build:    {cmd: "mvn -q -DskipTests compile"}          # parse: exit_code (default)
coverage: {cmd: "./scripts/cov.sh", parse: 'regex:Branch coverage: (?P<metric>[\d.]+)%', warn_below: 60, fail_below: 30}
lint:     {cmd: "./gradlew ktlintCheck", cwd: "backend"}  # cwd relativně k adaptéru
security: {builtin: true}                                # vestavěný secret scan
```

- Exit ≠ 0 → `fail`; exit 127 (příkaz neexistuje) → `unsupported`. S `regex:` se hledá pojmenovaná skupina `metric` ve stdout+stderr a porovná s `warn_below`/`fail_below` (procenta) nebo `warn_above`/`fail_above` (počty nálezů). Regex piš v jednoduchých uvozovkách. Volitelně `timeout` (s, default 600); gate lze zapsat i jako prostý řetězec.
- Gate v souboru chybí → `unsupported` („define in pflanzer.gates.yml"), do skóre se nepočítá. `null` gate explicitně vypne.

**Generátor.** `pflanzer init gates-template --path <repo> [--force]` detekuje stack a zapíše předvyplněný adaptér ze šablony `pflanzer.gates.yml.template` (aktivní jsou jen příkazy, které víme spustit; ostatní jsou zakomentované příklady). Lokální ověření bez DB: `python3 tool/cli/quality_gates.py --path <repo>`.

**Autodetekce bez adaptéru.** Node (`package.json`) a Python (`pyproject.toml`/`setup.py`) beze změny. Nově jako fallback: Maven (`pom.xml`), Gradle (`build.gradle[.kts]`, preferuje `./gradlew`), .NET (`*.sln`/`*.csproj`), Go (`go.mod`) — `build` + `tests`, u .NET a Go i `lint` (`dotnet format --verify-no-changes`, `go vet`). `security` = secret scan (i `.java/.kt/.cs/.go/.properties`); ostatní gates `unsupported`. Chybí binárka na PATH → `unsupported`.

**Přidání stacku.** V `quality_gates.py`: detekce `_is_<stack>_project` + pořadí v `detect_stack()`, příkazy do `STACK_COMMANDS`, jméno do `STACK_LABELS`/`OTHER_STACKS`. V `init.py`: větev v `_gate_presets()` (aktivní `gate` + zakomentovaný příklad `#gate`).

**Integrita.** Adaptér v repu může agent ve worktree „zjednodušit" (`tests: "true"`). Session 3 proto čte adaptér z base branche (`git show origin/main:pflanzer.gates.yml` do dočasného souboru) a předá ho přes `run_gates_on_path(path, adapter_path=…)` / CLI `--adapter <file>`; soubor ve worktree se pak ignoruje a `cwd` se řeší relativně ke kontrolované cestě. Dočasný soubor musí mít příponu `.yml`/`.json` (podle ní se parsuje).
Hlavička `quality-<variant>.md` uvádí zdroj gates (externí / ze stromu / autodetekce) se sha256. Změny `pflanzer.gates.yml` v main reviewuj jako změnu CI configu.

**`gates_run`.** Skóre nepočítá `unsupported` gates, takže 100/100 může stát na jediném gate. Výsledek proto nese `gates_run` (pass/warn/fail), `gates_unsupported` a v MD řádek „Gates run: N/9"; minimální počet pro verdikt řeší `session_3.py`.
