# Testing Standards

How tests are written and run in this project: a small headless runner (`tests/runner.gd`), a
base class with a handful of helpers (`tests/test_case.gd`), and one rule. **Every acceptance
criterion gets a test** (AGENTS.md rule 4).

The short version the model loads is the `godot-testing` skill. If this page and the skill disagree,
the skill wins.

Last checked: 2026-11-13. Every test on this page was run against Godot 4.7.2 with this repo's
runner, in a copy of the project with a coins/HUD/enemies feature built from
[PATTERNS.md](PATTERNS.md). The tests were also checked to **fail** when the feature is broken
(coin worth 5 instead of 10, no hit cooldown, restart removed).

---

## 1. Running tests

| Command | What runs |
| --- | --- |
| `bin/test.sh` | Every `tests/test_*.gd`, headless, at `--fixed-fps 60` |
| `bin/test.sh coins` | Only files or methods whose name contains `coins` |
| `bin/check.sh` | The whole gate: format, lint, import, parse, **tests**, smoke run |

Output is one line per test, then a summary:

```
PASS test_coins.gd::test_collecting_a_coin_adds_ten_to_the_score
FAIL test_coins.gd::test_a_coin_cannot_be_collected_twice: score after walking over the same spot again: expected 10, got 20

20 passed, 1 failed
```

`bin/test.sh` fails when:

- any test fails;
- no test ran (a filter that matches nothing, a file with no `test_` methods);
- the engine prints `SCRIPT ERROR`, `Parse Error`, a line starting with `ERROR:`, or a
  `WARNING: ... has vanished` (a broken scene), even if every test passed;
- one test runs longer than **3600 physics frames** (60 s of game time). The runner names it and
  stops;
- the whole run takes longer than **`TEST_TIMEOUT`** seconds (default 600). This catches a loop
  that never awaits, which the frame limit can't see.

That matters because Godot's own exit code is unreliable headless. A script that fails to load,
or a runtime error inside a callback, still exits 0. A runtime error can also skip `quit()` and
leave the process running forever. The output text plus time limits are the only safe check.

**`--fixed-fps 60`** makes every frame exactly 1/60 s of game time, however fast the machine runs.
So frame counts are deterministic: `hold_action("move_right", 60)` is one second of movement on
every run and every machine.

---

## 2. The harness

### Files

| File | Role | Edit? |
| --- | --- | --- |
| `tests/runner.gd` | Finds `test_*.gd`, runs each `test_*` method on a fresh instance with a frame limit, prints PASS/FAIL, exits 1 on failure or when nothing ran | **No** |
| `tests/test_case.gd` | Base class: `spawn`, `physics_frames`, `hold_action`, `tap_action`, `check`, `check_eq` | **No** |
| `tests/parse_check.gd` | Used by the gate's `parse` step to compile every script | **No** |
| `tests/scene_check.gd` | Used by the gate's `scenes` step to load and instance every scene | **No** |
| `tests/test_<thing>.gd` | Your tests, one file per feature or thing | Yes |

### Helpers: this is the complete list

| Helper | Does |
| --- | --- |
| `await spawn(path)` | Instance the scene under the root, make it `current_scene`, wait one frame (so `_ready()` has run), return it. Freed after the test |
| `await spawn(path, false)` | Same, but doesn't make it `current_scene` |
| `await physics_frames(n)` | Step `n` physics frames (60 = one second) |
| `await hold_action(action, frames)` | `Input.action_press`, step `frames` physics frames, release |
| `await tap_action(action)` | Hold for 1 frame, release, step 1 more frame |
| `check(condition, message)` | Record a failure if `condition` is false |
| `check_eq(actual, expected, message)` | Record a failure if they differ; the message shows both values |
| `tree` | The `SceneTree`, for `tree.get_nodes_in_group(...)`, `tree.current_scene` |
| `before_each()` / `after_each()` | Hooks you can override (see §5) |

There is no `check_gt`, `check_neq`, `key_press`, `wait_seconds`, `assert_eq` or `assert_true`.
Write `check(a > b, "...")` and put the values in the message.

### Always `await` the helpers

`spawn`, `physics_frames`, `hold_action` and `tap_action` are coroutines. **Called without
`await`, they return at once and the test carries on before anything has happened**: the player
hasn't moved, the scene hasn't loaded. Godot doesn't complain by default. The `missing_await`
warning catches it when set to error; see [GDSCRIPT_STYLES.md](GDSCRIPT_STYLES.md#warnings-as-errors).

```gdscript
await hold_action("move_right", 20)  # right: waits 20 physics frames
hold_action("move_right", 20)  # wrong: returns immediately, nothing moved yet
```

### `check` doesn't stop the test

A failed `check` records a message and the test **continues**. When later lines depend on
something that might be missing, guard them:

```gdscript
	var coin := tree.get_first_node_in_group("coins") as Node2D
	if coin == null:
		check(false, "there should be a coin")
		return
```

Otherwise the next line is a null access, which shows up as a `SCRIPT ERROR` instead of a clear
failure.

---

## 3. Shape of a test file

```gdscript
extends "res://tests/test_case.gd"
## Coins and score: five coins at start, collecting one adds 10 once and removes it.


func before_each() -> void:
	GameState.rng_seed = 1234  # same coin layout every run


func after_each() -> void:
	GameState.rng_seed = 0
	await super()


## Puts the player just left of a coin, clear of walls, ready to walk into it.
func _line_up_with(player: Node2D, coin: Node2D) -> void:
	player.global_position = coin.global_position + Vector2(-60, 0)
	await physics_frames(2)


func test_game_starts_with_five_coins() -> void:
	await spawn("res://scenes/main.tscn")
	check_eq(GameState.snapshot()["coins_left"], 5, "coins at start")


func test_no_coin_starts_on_the_player() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	var player := main.get_node("Player") as Node2D
	for coin: Node2D in tree.get_nodes_in_group("coins"):
		var gap := coin.global_position.distance_to(player.global_position)
		check(gap > 48.0, "coin at %s is %.0f px from the player" % [coin.global_position, gap])


func test_collecting_a_coin_adds_ten_to_the_score() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	var player := main.get_node("Player") as Node2D
	var coin := tree.get_nodes_in_group("coins")[0] as Node2D
	await _line_up_with(player, coin)
	await hold_action("move_right", 30)
	check_eq(GameState.score, 10, "score after one coin")


func test_a_collected_coin_is_removed() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	var player := main.get_node("Player") as Node2D
	var coin := tree.get_nodes_in_group("coins")[0] as Node2D
	await _line_up_with(player, coin)
	await hold_action("move_right", 30)
	check(not is_instance_valid(coin), "the collected coin should be freed")
	check_eq(tree.get_nodes_in_group("coins").size(), 4, "coins left")


func test_a_coin_cannot_be_collected_twice() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	var player := main.get_node("Player") as Node2D
	var coin := tree.get_nodes_in_group("coins")[0] as Node2D
	var spot := coin.global_position
	await _line_up_with(player, coin)
	await hold_action("move_right", 30)
	await hold_action("move_left", 20)  # walk back over where it was
	player.global_position = spot
	await physics_frames(5)
	check_eq(GameState.score, 10, "score after walking over the same spot again")
```

Conventions:

- **File:** `tests/test_<thing>.gd`, starting with `extends "res://tests/test_case.gd"` (a path,
  because the base class has no `class_name`).
- **Method names are sentences** saying what happens: `test_a_coin_cannot_be_collected_twice`.
  The runner only runs methods starting with `test_`. Helpers start with `_`.
- **One behaviour per test.** Several `check`s are fine when they describe one behaviour (the coin
  is gone *and* the count dropped). Unrelated behaviours go in separate tests, so a failure names
  the thing that broke.
- **Typed, tabs, gdformat-clean**, like all other GDScript. Tests go through the same format and
  lint steps.

---

## 4. What to assert on

In order of preference:

1. **`GameState`**: `GameState.score`, or `GameState.snapshot()["coins_left"]`. It's the source of
   truth, and it's what the playtest reads too, so test and playtest agree.
2. **Groups:** `tree.get_nodes_in_group("coins").size()`, `get_first_node_in_group("player")`.
3. **A node the scene owns directly**, by name or unique name: `main.get_node("Player")`,
   `hud.get_node("%Score")`.
4. **Never** private variables (`coin._taken`) or long paths (`get_node("Main/World/Things/Coin3")`).

**UI criteria are checked on the UI.** "The score is shown top-left as `Score: N`" is about the
label, so read the label. Don't copy display text into `GameState` to dodge it:

```gdscript
func test_score_label_shows_the_score() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	GameState.collect_coin(10)
	await physics_frames(1)
	var label := main.get_node("HUD").get_node("%Score") as Label
	check_eq(label.text, "Score: 10", "score label text")


func test_score_label_is_top_left() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	var label := main.get_node("HUD").get_node("%Score") as Label
	var rect := label.get_global_rect()
	check(rect.position.x < 100 and rect.position.y < 100, "label at %s" % rect.position)
```

What the label *looks* like (readable, not covered) is the playtest's job, with a screenshot.

**Check the effect and the absence of the wrong effect.** The score went up by exactly 10. The
coin is gone. Walking over the spot again adds nothing.

**A test must fail when the feature is missing.** Before calling a test done, imagine deleting the
feature's code (or actually do it). If the test would still pass, it tests nothing. A test that
only checks "no errors" or `score >= 0` proves nothing.

---

## 5. Isolation: what the harness resets and what it doesn't

After each test, `after_each()` releases every input action, frees every scene `spawn()` created,
and waits a frame. It does **not**:

- **Reset `GameState`.** In this project `main.gd` calls `GameState.reset()` in `_ready()`, so
  every test that spawns main starts fresh. A test that spawns some other scene, or none, gets
  whatever the last test left. Call `GameState.reset()` yourself first.
- **Free nodes your test created another way.** A node added with `main.add_child(...)` goes when
  main goes. But `get_tree().reload_current_scene()` or `change_scene_to_file()` makes a **new**
  scene the harness doesn't know about, and you must free it:

```gdscript
func test_restart_after_game_over_resets_the_game() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	GameState.collect_coin(10)
	GameState.damage_player(3)
	await tap_action("restart")
	await physics_frames(2)  # reload_current_scene() swaps the scene at the end of the frame
	var fresh := tree.current_scene
	check(fresh != main and fresh != null, "a new main scene should be current")
	check_eq(GameState.score, 0, "score after restart")
	check_eq(GameState.health, 3, "health after restart")
	if fresh:
		fresh.queue_free()  # the harness only frees scenes spawn() created
```

- **Undo settings you changed.** If you override `before_each()` to change configuration, undo it
  in `after_each()`, and **`await super()`** there so the harness cleanup still runs (see the
  `rng_seed` example in §3).
- **Disconnect your signal connections** to autoloads. A lambda connected to `GameState.changed`
  outlives the test. Connections to a node's own methods go when the node is freed; lambdas
  don't belong to a node. Connect lambdas only to signals on nodes the test spawned, or
  `disconnect` at the end.

**Never** rely on test order. Each test method gets a fresh instance of the file's class, and
files run alphabetically, but a test that passes only after another test is broken.

---

## 6. Timing

Things happen across frames, and most flaky tests come from asserting too early.

| Situation | Wait |
| --- | --- |
| After `spawn()` | Nothing extra: `_ready()` has run |
| After teleporting a body (`global_position = ...`) | `await physics_frames(2)` before relying on overlaps |
| An `Area2D` overlap (`body_entered`) | At least **2** physics frames after the bodies touch |
| `queue_free()` | Takes effect at the end of the frame. `is_instance_valid(x)` is false after one frame |
| `add_child.call_deferred(...)` / `set_deferred(...)` | One frame |
| `reload_current_scene()` / `change_scene_to_file()` | One to two frames. Then read `tree.current_scene` again |
| `Input.is_action_just_pressed` in game code | `tap_action()` already holds for one physics frame |
| Something after N seconds of game time | `N * 60` physics frames, plus a few |

**Wait for a condition, with a limit**, instead of guessing a frame count, when the timing isn't
the thing under test:

```gdscript
## Steps physics frames until condition() is true or max_frames pass. Returns whether it came true.
func _wait_until(condition: Callable, max_frames: int) -> bool:
	for i in max_frames:
		if condition.call():
			return true
		await physics_frames(1)
	return condition.call()


func test_touching_an_enemy_costs_one_health_per_second() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	var player := main.get_node("Player") as Node2D
	var enemy := EnemyScene.instantiate() as Node2D
	enemy.position = player.position + Vector2(40, 0)
	main.add_child(enemy)
	var hit := await _wait_until(func() -> bool: return GameState.health < 3, 60)
	check(hit, "the enemy should hit within a second")
	check_eq(GameState.health, 2, "health right after the first hit")
	await physics_frames(30)
	check_eq(GameState.health, 2, "no second hit inside the cooldown")
```

When the timing **is** the criterion ("an enemy appears every 3 seconds"), check both sides of it:

```gdscript
func test_first_enemy_spawns_after_three_seconds() -> void:
	await spawn("res://scenes/main.tscn")
	await physics_frames(170)
	check_eq(tree.get_nodes_in_group("enemies").size(), 0, "enemies before 3 s")
	await physics_frames(20)
	check_eq(tree.get_nodes_in_group("enemies").size(), 1, "enemies just after 3 s")
```

Never `OS.delay_msec()` or real-time timers in tests: they don't advance game time headless.

**Count game time in physics frames** in game code that tests depend on (cooldowns, spawn
intervals). Under `--fixed-fps 60` a `Timer` also works, but a frame counter is simplest to test
exactly.

---

## 7. Input

`hold_action` and `tap_action` use `Input.action_press()` / `action_release()`. That is what
`Input.is_action_pressed()`, `is_action_just_pressed()` and `Input.get_vector()` read, so it
drives anything written per AGENTS.md rule 3.

- **It does not call `_input()` / `_unhandled_input()`.** Game code that reacts to input
  *events* won't see `action_press`. Either read input by polling in `_process` /
  `_physics_process` (preferred here), or send a real event in the test:

  ```gdscript
  	var event := InputEventAction.new()
  	event.action = "restart"
  	event.pressed = true
  	Input.parse_input_event(event)
  	Input.flush_buffered_events()
  ```

- **Diagonals:** `Input.action_press("move_up")`, `Input.action_press("move_right")`,
  `await physics_frames(n)`, then release both. `after_each()` releases everything anyway.
- **Pressing and releasing in the same frame does nothing** to code that polls in
  `_physics_process`. Hold for at least one physics frame; `tap_action` does.
- **Set positions directly** only to skip travel the test isn't about (the `_line_up_with`
  helper above). The move that the criterion is about should be real input.

---

## 8. Randomness

Random placement or behaviour makes tests flaky unless the test controls the seed. In this
project, game code draws from **`GameState.rng`**, a `RandomNumberGenerator`, never from global
`randf()` / `randi()`. `GameState.reset()` seeds it from `GameState.rng_seed` (0 = random). A test
that depends on the layout sets the seed in `before_each()` and clears it in `after_each()`
(§3). See [PATTERNS.md](PATTERNS.md#gamestate).

Better still, **write tests that don't care where things are**: read the coin's position from the
group and walk to it, as `_line_up_with` does. Then the test passes for every seed, and the seed
only makes failures reproducible.

The same seed gives the same sequence on the same Godot version. It isn't guaranteed across
engine versions, so never hard-code positions that come from a seed.

---

## 9. Signals

Connect a lambda that **appends to an Array**, act, then check the array:

```gdscript
func test_collecting_emits_changed_once() -> void:
	var main: Node = await spawn("res://scenes/main.tscn")
	var player := main.get_node("Player") as Node2D
	var coin := tree.get_nodes_in_group("coins")[0] as Node2D
	await _line_up_with(player, coin)
	var emissions: Array[int] = []  # an Array, because lambdas capture ints by value
	GameState.changed.connect(func() -> void: emissions.append(GameState.score))
	await hold_action("move_right", 30)
	check_eq(emissions, [10] as Array[int], "changed emissions (score at each)")
```

**Lambdas capture local variables by value.** `var count := 0` with `count += 1` inside the lambda
leaves the outer `count` at 0, silently (checked on 4.7.2). Arrays and Dictionaries are
references, so appending works.

This example connects a lambda to an autoload, so the connection outlives the test (§5). It's
harmless here because the lambda only appends to a local array. Don't leave lambdas on autoload
signals that touch nodes.

---

## 10. Pure logic: test without a scene

Rules that are just numbers (damage formulas, scoring, level thresholds) go in `static func`s
([ARCHITECTURE.md](ARCHITECTURE.md#4-pure-rules-static-functions)). Their tests need no scene and
run instantly:

```gdscript
extends "res://tests/test_case.gd"
## Pure rules: no scene needed.


func test_armor_reduces_damage() -> void:
	check_eq(Rules.damage_after_armor(5, 2), 3, "5 damage against 2 armour")


func test_a_hit_always_does_at_least_one() -> void:
	check_eq(Rules.damage_after_armor(1, 10), 1, "1 damage against 10 armour")
```

Cover the edges there (zero, negative, caps). Then the slower scene tests only need to show that
the rule is wired in.

---

## 11. Tests and the playtest

Each feature is checked twice: these tests in `bin/check.sh`, then a playtest that runs the real
game through the godot MCP (`godot-playtest` skill). They catch different
things:

| | Headless tests | Playtest |
| --- | --- | --- |
| Runs | Every gate, in seconds | Once per feature, in a real window |
| Sees | `GameState`, nodes, groups, label text | The rendered screen (screenshots), debug output |
| Catches | Logic, counts, timing, regressions | Invisible or covered UI, wrong colours, things off-screen, errors only a real window shows |
| Can't do | Rendering: headless uses a dummy renderer, so no screenshots | Exact timing; it's slow |

Both read `GameState.snapshot()`. Anything a criterion needs is in it (AGENTS.md rule 1).

---

## 12. When `bin/test.sh` fails

| Output | Meaning | Fix |
| --- | --- | --- |
| `FAIL file::method: message` | A `check` failed; the message has the values | Fix the code, or the test if the test is wrong |
| `FAIL file: does not load (parse error above?)` | The test file doesn't compile | The `SCRIPT ERROR: Parse Error` line above names the file and line |
| `SCRIPT ERROR: ...` with all tests passing | A runtime error somewhere (often a null access in a callback) | Fix it. The run fails anyway, on purpose |
| `test.sh: the engine reported errors above` | An `ERROR:` line, e.g. a `push_error`, a missing resource, a bad scene | Read the first `ERROR:` line |
| `"await" keyword might be desired because the expression is a coroutine` | A helper called without `await` (`missing_await` is an error here) | Add `await` |
| `FAIL no tests ran` | The filter matches no file or method, or there are no `test_*` methods | Check the filter and the names (`test_*.gd`, `func test_...`) |
| `FAIL file::method: still running after 3600 physics frames; stopping the run here` | That test awaits something that never happens (a signal that doesn't fire, a node that never appears) | Find out why it didn't happen; wait with a frame limit (§6) |
| `TIMEOUT: still running after 600s` | The whole run was stopped, usually by a `while` loop that never awaits | The test after the last PASS/FAIL line hung |

---

## 13. Beyond this runner

The custom runner is deliberate: nothing to version-pin against Godot releases, and output a model
parses easily. If the project outgrows it (it needs orphan-node checks, signal watchers, JUnit
output for CI), the maintained frameworks as of November 2026 are:

| Framework | Godot 4.7 support | Headless CLI |
| --- | --- | --- |
| [GUT](https://github.com/bitwes/Gut) | 9.7.x (`godot_4_7` branch) | `godot --headless -s addons/gut/gut_cmdln.gd -gdir=res://test -gexit` |
| [gdUnit4](https://github.com/godot-gdunit-labs/gdUnit4) | 6.2.x (Godot 4.5 to 4.7.1); 7.0 in development | `addons/gdUnit4/runtest.sh -a res://test` (exit 100 on failure) |

Switching frameworks is a harness change (AGENTS.md: the model doesn't edit the harness), so it's a
decision for the repo owner. Whatever runs the tests, keep this runner's properties: a per-test
limit, failing when nothing ran, and failing on engine errors in the output.

### CI sketch

To run the gate in GitHub Actions, install Godot with
[chickensoft-games/setup-godot](https://github.com/chickensoft-games/setup-godot) (full version,
`use-dotnet: false`), cache `.godot/` keyed on `project.godot` and the `*.import` files, and run
`bin/check.sh`. It already greps for engine errors instead of trusting exit codes. Screenshots need
a display, so a playtest-like step on Linux runs under `xvfb-run` without `--headless`.

---

## Checklist

- [ ] Every acceptance criterion has a named test, and the test fails without the feature
- [ ] Every helper call is `await`ed
- [ ] Assertions read `GameState`, groups, or a directly owned node; never private vars
- [ ] Waits are long enough for overlaps (2+ physics frames), or use a condition with a limit
- [ ] Randomness comes from `GameState.rng`; tests don't depend on a specific layout
- [ ] Anything the test changed that the harness doesn't reset is undone
- [ ] `bin/test.sh` shows the new tests as `PASS`, and `bin/check.sh` passes
