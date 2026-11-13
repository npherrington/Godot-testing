# Godot Lab

A 2D Godot game built with one local model in OpenCode (via Ollama). You write a feature file; the
model plans it, builds it, runs the gate, playtests it in the running game and reviews its own
diff, all in one session. You commit.

## Setup (once)

```bash
brew install --cask godot     # Godot 4.7+
brew install opencode
bin/setup.sh                  # pinned godot-mcp-runtime + gdtoolkit, imports the project
bin/check.sh                  # should print seven "ok" lines
```

Ollama must be running with the model named in `opencode.jsonc`, with enough context for a coding
agent. The default can be as low as 4k tokens, and a model that runs out "forgets" the plan:

```bash
OLLAMA_CONTEXT_LENGTH=65536 ollama serve
ollama ps                     # once the model is loaded: CONTEXT should read 65536
```

## Building a feature

1. Write `features/NNNN-name.md` from `features/TEMPLATE.md`, or run `opencode` and type
   `/spec <idea>`. Acceptance criteria must be checkable: numbers, counts, text on screen.
   Three to six criteria per file; split bigger ideas into several files.
2. In `opencode`, run `/feature features/NNNN-name.md`. It writes `runs/<name>/plan.md` and stops
   so you can check its decisions. Say go, and it builds, runs `bin/check.sh` until it passes,
   playtests each criterion in the running game, and reviews its own diff.
3. Play it yourself: `bin/godot --path .`, or open the project in the Godot editor. Then commit.

Start a **new session for each feature**. A local model does best with a short context, and the
plan file in `runs/` carries everything forward if a session has to restart.

Other commands: `/playtest <feature file or description>` checks the running game without changing
anything.

## How it fits together

| Piece | Where | Role |
| --- | --- | --- |
| Rules | `AGENTS.md` | Loaded every session: commands, layout, the build steps, the rules |
| Skills | `.opencode/skills/` | Short guides the model loads when it needs them: GDScript style, `.tscn` by hand, tests, playtesting, plans, feature files |
| Commands | `.opencode/commands/` | `/spec`, `/feature`, `/playtest` |
| Gate | `bin/check.sh` | Format, lint, import, parse, scenes, tests, smoke run: the definition of done. Strict GDScript warnings (`project.godot` `[debug]`) are errors |
| Tests | `tests/` | Headless runner; `bin/test.sh [filter]` |
| Game driver | `godot` MCP (godot-mcp-runtime, pinned in `tools/`) | Run the game, send input, read state, take screenshots |
| Reference | `docs/` | The long versions, for you. Start at [docs/DESIGN.md](docs/DESIGN.md) |

To change the model, edit `"model"` in `opencode.jsonc`. Nothing else names it.
