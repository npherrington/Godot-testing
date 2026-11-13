# Agentic Coding in Godot

How coding agents build and verify a Godot game without a human watching: what works, what lies
to you, and how this repo is set up for it. This is the state of things in **November 2026**:
Godot 4.7.2, gdtoolkit 4.5.0, godot-mcp-runtime 4.0.1, OpenCode with local Ollama models.

Two kinds of claim appear here. **Checked** means it was run on 2026-11-13 against this repo's
Godot 4.7.2 and tools. **Reported** means it comes from documentation or research, with the source
linked. Unmarked statements describe this repo, and can be checked by reading it.

---

## 1. Why Godot suits agents, and where it bites

**What helps:**

- **Everything is text.** Scenes (`.tscn`), resources (`.tres`), settings (`project.godot`) and
  scripts are all diffable text an agent can read and write.
- **It runs headless.** Import, compile, tests and a smoke run all work from the command line,
  without a window, in seconds.
- **The compiler is good.** With static typing, Godot 4.7's analyzer catches type errors,
  missing members and Godot 3 syntax. It says what to use instead (§5).
- **State can be read live.** An MCP bridge can run GDScript inside the running game and return
  JSON (§4).

**What bites:**

- **Training data is mostly Godot 3.** Models write `yield`, `export var`, `KinematicBody2D` and
  `instance()`. The syntax ones fail to compile; renamed *methods* compile and fail at runtime
  (§5).
- **Exit codes lie.** **Checked:** `godot --check-only -s broken.gd` prints a parse error and exits
  **0**. `--import` with a script that doesn't compile exits 0. A runtime `SCRIPT ERROR` aborts
  only the current function, so in a `-s` script it can skip the `quit()` call and leave the
  process **running forever**. The only reliable signals are the output text and a timeout.
  So this repo's harness never trusts either one alone:
  - `bin/check.sh` and `bin/test.sh` grep the output for `SCRIPT ERROR`, `Parse Error`,
    `ERROR:` and `WARNING: ... has vanished`.
  - **Every Godot run has a time limit** (`bin/with-timeout.sh`, which stops the whole process
    tree). The defaults are import 300 s, parse, scenes and smoke 120 s each, and tests 600 s. Each
    can be overridden with `IMPORT_TIMEOUT` and similar variables.
  - Inside the test run, `tests/runner.gd` fails a test still running after **3600 physics
    frames** (60 s of game time), names it, and stops the run.
  - In `bin/build-feature.sh`, each agent phase is stopped after `--phase-timeout` minutes
    (default 90).
- **Some scene mistakes are only warnings.** **Checked:** a `parent=` naming a missing node, or a
  node missing its `type=`, prints a `WARNING: ... vanished` and drops the node. Godot's exit code
  doesn't change, so the gate fails on that warning text. The `scenes` step also loads and
  instances every `.tscn`, including ones nothing uses yet
  ([SCENES_AND_TSCN.md](SCENES_AND_TSCN.md#what-godot-says-when-a-scene-is-wrong)).
- **Headless means no pixels.** The dummy renderer gives no screenshots, so anything visual needs
  a real window (§4).
- **The text format moved.** Godot stopped writing `load_steps` in 4.6 and started writing
  `unique_id` on nodes. Uids and `.uid` sidecars came in 4.4. Models trained earlier get all of
  these wrong ([SCENES_AND_TSCN.md §1](SCENES_AND_TSCN.md#what-not-to-write)).

---

## 2. The loop

Agents do well in Godot when every change goes through a tight loop, **write, gate, run, look**,
and each step's output is fed back verbatim.

### How this repo runs it

`bin/build-feature.sh features/NNNN-name.md` runs each phase as a fresh `opencode run` session,
with its own agent and only the tools that agent needs:

| Phase | Agent | Reads | Writes | Tools |
| --- | --- | --- | --- | --- |
| Plan | `planner` | feature file, scenes, scripts | `runs/<f>/plan.md` (every name, path, number) | files |
| Implement | `implementer` | plan, skills | scripts, scenes, tests | files, shell, `bin/check.sh` |
| Gate | (script) | | `runs/<f>/check.txt` | `bin/check.sh` |
| Playtest | `playtester` | criteria, plan's playtest notes | verdict + screenshots | **godot MCP** |
| Review | `reviewer` | diff, criteria, AGENTS.md | APPROVE / CHANGES | files |

A failed gate, a `VERDICT: FAIL` or a `CHANGES` review goes back to the implementer, up to
`--max-fixes` rounds (default 4). Phases pass work through `runs/<f>/handoff.md`, never through
shared context. That keeps each session small enough for a local model.

### Why it's shaped like this

- **Fresh sessions per phase.** Local models degrade as context fills. A planner that already
  read everything hands over a short, exact plan, and the implementer starts clean.
- **The plan names everything** (`feature-plan` skill): every node, group, signal, file and number.
  A smaller implementer model follows instructions well and invents badly.
- **The gate is the definition of done** (AGENTS.md). Agents don't argue with it; they read it.
- **Tests and playtest both**, because they catch different failures
  ([TESTING_STANDARDS.md §11](TESTING_STANDARDS.md#11-tests-and-the-playtest)).
- **A separate reviewer** catches what passes every check but breaks a rule: long node paths,
  state outside `GameState`, scope creep.

---

## 3. The verification ladder

Each rung catches things the ones below it can't. Run them in this order; stop at the first failure
and fix that.

| Rung | Command | Catches | Misses |
| --- | --- | --- | --- |
| Format | `gdformat --check` (`bin/format.sh` fixes) | Spacing, blank lines, wrapping | Everything semantic |
| Lint | `gdlint` | Naming, declaration order, unused args, long lines and functions | Types, API misuse |
| Import | `godot --headless --path . --import` | Broken resources, missing files, scripts that fail to load | Scripts and scenes nothing loads yet |
| Parse | `tests/parse_check.gd` over every `.gd` | Compile errors in *every* script, including unused ones, with strict warnings as errors | Runtime behaviour |
| Scenes | `tests/scene_check.gd` over every `.tscn` | Scenes that don't load or instance, dropped nodes (`has vanished`), duplicate sibling names, including unused scenes | What `_ready()` does |
| Tests | `bin/test.sh` | Behaviour, counts, timing, regressions | How it looks |
| Smoke | main scene, 180 frames, headless | Errors on startup and in the first 3 s | Anything later or interactive |
| Playtest | godot MCP in a real window | Visibility, layout, colour, real input feel | Exact timing; it's slow |
| Review | a reading agent | Rule breaks, scope, design smells | Anything it doesn't read |

The first seven are `bin/check.sh`, each Godot step with a time limit. Feed a failing step's
**exact output** back to the agent.
Godot 4.7's messages are specific enough to act on directly. **Checked:**

```
"yield" was removed in Godot 4. Use "await" instead.
Function "is_key()" not found in base Dictionary.
"await" keyword might be desired because the expression is a coroutine. (Warning treated as error.)
[ext_resource] referenced non-existent resource at: res://scripts/playr.gd.
```

### Make the compiler strict

Godot ships with most type-safety warnings **off**, and headless runs only fail on warnings set to
**error**. This repo's `project.godot` turns these up, so the gate catches far more agent mistakes:

```ini
[debug]

gdscript/warnings/untyped_declaration=2
gdscript/warnings/unsafe_property_access=2
gdscript/warnings/unsafe_call_argument=2
gdscript/warnings/unsafe_cast=2
gdscript/warnings/missing_await=2
```

**Checked:** the repo, and a coins/HUD/enemies build made from [PATTERNS.md](PATTERNS.md), pass
the whole gate with these on. `missing_await=2` turns the most common test bug (calling
`hold_action` without `await`) into a compile error.

They also apply to the playtester's `run_script` code, which the MCP bridge compiles inside the
game. `return scene_tree.get_first_node_in_group("player").global_position` is rejected, and
`(... as Node2D).global_position` works. The `godot-playtest` skill says so. The bridge script
itself suppresses warnings, so it is unaffected.

`unsafe_method_access=2` would also catch hallucinated Godot 3 method names (`change_scene()`,
`instance()`), but `tests/test_case.gd` calls `load(path).instantiate()` on an untyped
`Resource`, so it stays off for now.

These levels are part of the gate. AGENTS.md tells agents never to lower them, and the reviewer
checks diffs against AGENTS.md.

---

## 4. Giving agents eyes: the godot MCP

The playtester drives the real game through **[godot-mcp-runtime](https://github.com/Erodenn/godot-mcp-runtime)**
(npm, pinned to 4.0.1 in `tools/package.json`, configured in `opencode.jsonc`). It needs Node 20+
and Godot 4.5+.

**How it works** (read from the pinned package's source): `run_project` launches the game with a
temporary `McpBridge` autoload added to `project.godot`. The bridge listens on localhost TCP and is
removed when the game stops. Runtime tools talk to it.

| Tool | Use | Notes |
| --- | --- | --- |
| `run_project` / `stop_project` | Start (in the background) and always stop | One game at a time per project |
| `run_script` | Run GDScript inside the game; the return value comes back as JSON | Source must `extends RefCounted` with `func execute(scene_tree: SceneTree) -> Variant`. It may `await`. Compiled under the project's warning settings |
| `simulate_input` | Batches of `action`, `key`, `mouse_button`, `click_element`, `text`, `wait` (ms or frames) | `"watch": ["/root/GameState:score"]` samples up to 16 properties after each step |
| `take_screenshot` | PNG to `.mcp/godot-runtime/screenshots/` plus a 960×540 preview | Also returns colour stats with a `likelyBlank` flag, so a model without vision can spot a blank frame |
| `get_ui_elements` | Visible `Control`s with their text and rects | Cheaper than a screenshot for "is the label there and what does it say" |
| `get_debug_output` | The game's log | Any `SCRIPT ERROR` fails the playtest |

The package has 43 tools in all, including headless scene editing (`create_scene`, `add_node`,
`save_scene`), profiling and project settings. Each tool's schema costs context, so `opencode.jsonc`
denies `godot_*` to every agent except the playtester.

**Rules of thumb:**

- **Numbers first, pictures second.** Read `GameState.snapshot()` with `run_script` for anything a
  number answers. Screenshots are **evidence** for visual criteria, not the oracle: a run can report
  success while its screenshot shows something else.
- **Screenshots need a real, visible window.** Not `--headless`, not minimised. On Linux CI, use
  `xvfb-run` with the `gl_compatibility` renderer (this project's setting).
- **Check that input landed** (watch a value) before trusting the result of a sequence.
- **Check `project.godot` before committing** if a playtest crashed. A run that dies before
  `stop_project` can leave the `McpBridge` autoload entry behind. The server sweeps stranded
  entries the next time it starts (`dist/sweep-stranded.js`), but a commit made in between would
  include it. `git diff project.godot` shows it.

### Other Godot MCP servers (November 2026, **reported**)

| Server | Kind | Can it see the running game? | Notes |
| --- | --- | --- | --- |
| [godot-mcp-runtime](https://github.com/Erodenn/godot-mcp-runtime) | Node, launches Godot | **Yes**: input, scripts, screenshots | Used here. MIT |
| [Coding-Solo/godot-mcp](https://github.com/Coding-Solo/godot-mcp) | Node, CLI | No (console output only) | 14 tools: run, scenes, uids |
| [Godot AI (hi-godot)](https://github.com/hi-godot/godot-ai) | Python + editor plugin | Yes, via the editor | Godot 4.7+. Sends telemetry by default (`GODOT_AI_DISABLE_TELEMETRY=true`) |
| GDAI MCP | Editor plugin | Yes, via the editor | Proprietary licence |
| LSP- and docs-based servers | Diagnostics, offline API docs | No | Useful alongside a runtime server |

Editor-plugin servers need the Godot editor open, which doesn't suit unattended runs. That's why
this repo uses a server that launches the game itself.

---

## 5. Godot 3 habits and hallucinated APIs

The full table is in [GDSCRIPT_STYLES.md §6](GDSCRIPT_STYLES.md#6-godot-4-api-not-godot-3). The
key point for agents is **which mistakes the compiler catches**. **Checked** on 4.7.2:

| Caught at compile time (gate fails) | **Not** caught (fails at runtime, or never) |
| --- | --- |
| `yield`, `export var`, `onready var`, `tool`, `setget` | `get_tree().change_scene(path)` |
| `extends KinematicBody2D`, `Sprite`, `Position2D` | `packed_scene.instance()` on an untyped value |
| `move_and_slide(vel, Vector2.UP)` (too many args) | `node.update()` |
| `connect("sig", self, "method")` | Methods on untyped variables (`var a = []` then `a.empty()`) |
| `Type?`, `for k, v in d`, `d.is_key()`, `@staticmethod`, `Array[int]()` | Wrong node paths in `$` / `get_node` |
| A `class_name` that hides an autoload | Signals that are declared but never connected |

The right column is why **typing matters more for agents than for people**. On a typed variable
the analyzer knows the class and rejects a missing method. On an untyped one it assumes a subclass
might add it. The tests and the playtest catch the rest.

---

## 6. Give the model the real API

Don't let the model guess at signatures. Godot dumps its own reference, matched exactly to the
installed version. **Checked:**

```bash
# Every engine class as XML (1076 files): doc/classes/CharacterBody2D.xml, ...
bin/godot --headless --doctool /tmp/godot-ref

# One JSON file (~12 MB) with every class, method signature, property and description
bin/godot --headless --dump-extension-api-with-docs     # writes ./extension_api.json

# This project's own scripts, from their ## doc comments
bin/godot --headless --path . --gdscript-docs res://scripts --doctool /tmp/project-ref
```

Grep one class's XML into the prompt when an agent is unsure of an API, rather than pasting the
whole thing:

```bash
grep -A3 '<method name="move_and_slide"' /tmp/godot-ref/doc/classes/CharacterBody2D.xml
```

Keep these dumps **outside the repo**; they're large and version-specific. Godot publishes no
`llms.txt` (reported).

---

## 7. Local and small models

This pipeline runs on local models through Ollama (`opencode.jsonc`; each agent's model is in
`.opencode/agents/*.md`, or set for a whole run with `--model=`).

- **Context length is the first thing to check.** Ollama's default depends on VRAM, and can be as
  low as 4k tokens. Ollama recommends **at least 64k for agents and coding tools** (reported, from
  [docs.ollama.com/context-length](https://docs.ollama.com/context-length)). Set it server-wide
  with `OLLAMA_CONTEXT_LENGTH=65536 ollama serve`, and confirm it in the `CONTEXT` column of
  `ollama ps`. A truncated context looks like an agent "forgetting" the plan halfway through.
- **Fewer tools, smaller prompts.** Every MCP tool schema is context. Deny what a phase doesn't
  need (this repo denies the 43 godot tools to all but the playtester), and let plain tool calls
  do the work (`"codemode": false`).
- **Skills over docs.** Agents load the short `.opencode/skills/*` files. These `docs/` pages are
  the long form, for people and for planning; don't load them all into an implementer's context.
- **Exact plans.** The planner may be bigger than the implementer. Every name and number decided
  up front means the implementer never has to design.
- **Feed errors back verbatim**, one at a time, first error first. Godot's cascading errors
  (one bad scene line produces five messages) confuse small models when given all at once.
- **Bound everything.** Fix rounds (`--max-fixes`), playtest input batches (under about 20 s),
  retries in game code, waits in tests. A small model in a loop with no limit burns the night,
  and so does a gate that hangs (§1).

---

## 8. Agent pitfalls specific to Godot

| Pitfall | Do this instead |
| --- | --- |
| New script committed without its `.gd.uid` | The import step creates it; `git add` both. Move or rename them together (`git mv`) |
| Editing `.godot/` | Never. It's the import cache, ignored by git. Deleting it is safe and fixes stale "class not found" errors |
| `load_steps`, invented `uid://...`, `unique_id` in hand-written scenes | Leave them out; Godot fills in what it wants |
| Adding or freeing physics nodes inside `body_entered` | `queue_free()`, `add_child.call_deferred()`, `set_deferred()` |
| Global `randf()` in game code | `GameState.rng`, seeded in `reset()` |
| Reading `_input()` events in game code | Poll actions in `_process` / `_physics_process`, so tests and the MCP can drive them |
| Path case (`res://Scenes/Coin.tscn`) | Exact case. macOS forgives it; Linux CI doesn't |
| `print()` left in for debugging | Remove it. Noisy output hides real errors from the next agent |
| Trusting "All tests passed" | Trust `bin/check.sh`, which also fails on any engine error in the output |
| Leaving the game running after a playtest | Always call `stop_project`, pass or fail |

---

## 9. Godot's policy on AI

The Godot Foundation's 2026 contribution policy (reported,
[godotengine.org/article/contribution-policy-2026](https://godotengine.org/article/contribution-policy-2026/),
June 2026) bans autonomous agents and AI-generated code in **pull requests to the engine
itself**. It says nothing about games made *with* Godot, and the MIT licence doesn't restrict them.
Godot ships no first-party AI features; AI tooling is third-party add-ons and MCP servers.

---

## Sources

- Godot 4.7 command line: <https://docs.godotengine.org/en/4.7/tutorials/editor/command_line_tutorial.html>
- GDScript style guide: <https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_styleguide.html>
- Static typing and warnings: <https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/static_typing.html>
- TSCN format: <https://docs.godotengine.org/en/stable/engine_details/file_formats/tscn.html>
- Upgrading from Godot 3: <https://docs.godotengine.org/en/stable/tutorials/migrating/upgrading_to_godot_4.html>
- Release notes: <https://godotengine.org/releases/4.5/>, <https://godotengine.org/releases/4.6/>, <https://godotengine.org/releases/4.7/>
- UIDs in 4.4: <https://godotengine.org/article/uid-changes-coming-to-godot-4-4/>
- Input class: <https://docs.godotengine.org/en/4.7/classes/class_input.html>
- gdtoolkit changelog: <https://github.com/Scony/godot-gdscript-toolkit/blob/master/CHANGELOG.md>
- godot-mcp-runtime: <https://github.com/Erodenn/godot-mcp-runtime>
- Ollama context length: <https://docs.ollama.com/context-length>
