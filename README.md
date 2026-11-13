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

Ollama must be running with the model named in `opencode.jsonc`: Devstral Small 2 24B (Q8) with
its context capped at 64k. Uncapped, Ollama picks a context size from your memory. That can be
too small (the model "forgets" the plan) or too big (256k, 69 GB, half on the CPU). The cap is
baked into a model variant, so it holds however Ollama is started:

```bash
ollama pull devstral-small-2:24b-instruct-2512-q8_0
printf 'FROM devstral-small-2:24b-instruct-2512-q8_0\nPARAMETER num_ctx 65536\n' > /tmp/Modelfile
ollama create devstral-small-2:24b-64k -f /tmp/Modelfile    # shares the weights; no extra disk
ollama run devstral-small-2:24b-64k ok && ollama ps         # CONTEXT 65536, PROCESSOR 100% GPU
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

To change the model, edit the top of `opencode.jsonc` (`model`, `small_model`, and its entry under
`provider`). Nothing else names it. Give any new model a 64k variant the same way.
