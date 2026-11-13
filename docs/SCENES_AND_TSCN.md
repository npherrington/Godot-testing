# Scenes and `.tscn` Files

In this project, agents write scenes as text, without the editor. Godot is strict about the
format, and a bad scene fails the gate's `import` step. This page covers the format as Godot
**4.7.2** reads and writes it, the rules that keep hand-written scenes loading, and how scenes are
organised here.

The short version agents load is the `godot-scenes` skill (`.opencode/skills/godot-scenes/`). If
this page and the skill disagree, the skill wins.

Last checked against the engine: 2026-11-13 (scenes resaved with Godot 4.7.2 `ResourceSaver` to see
what the engine writes today).

---

## 1. The format

```ini
[gd_scene format=3]

[ext_resource type="Script" path="res://scripts/coin.gd" id="1_coin"]

[sub_resource type="CircleShape2D" id="CircleShape2D_coin"]
radius = 10.0

[node name="Coin" type="Area2D" groups=["coins"]]
script = ExtResource("1_coin")

[node name="Body" type="Polygon2D" parent="."]
color = Color(1, 0.84, 0.2, 1)
polygon = PackedVector2Array(-8, -8, 8, -8, 8, 8, -8, 8)

[node name="Collision" type="CollisionShape2D" parent="."]
shape = SubResource("CircleShape2D_coin")
```

Sections, in this order, each followed by a blank line:

1. **`[gd_scene format=3]`**, the header. `format=3` is the Godot 4 text format. There is no
   format 4.
2. **`[ext_resource ...]`**: files this scene uses (scripts, other scenes, textures).
   `type`, `path` and `id` are required.
3. **`[sub_resource ...]`**: resources embedded in this file (shapes, materials, styles). The
   properties go on the lines below.
4. **`[node ...]`**: the tree, parents before children. The first node is the root.
5. **`[connection ...]`**: signal connections, if any. This project connects in code instead
   (see [GDSCRIPT_STYLES.md §9](GDSCRIPT_STYLES.md#9-godot-specific-habits)).

### Rules that keep it loading

- **ids are unique within the file**, and every `ExtResource("id")` / `SubResource("id")` refers to
  an id defined **above** it. Ids are just strings. Use readable ones: `"1_coin"`,
  `"CircleShape2D_coin"`.
- **The root `[node]` has no `parent`.** Its direct children use `parent="."`. Grandchildren use the
  child's name (`parent="Walls"`); deeper nodes use a path from the root (`parent="Walls/Top"`).
- **Node names are unique among their siblings.**
- **Values are Godot literals:** `Vector2(1, 2)`, `Color(r, g, b, a)` with channels from 0 to 1,
  `PackedVector2Array(...)`, `true`, floats written with `.0` where the property is a float
  (`radius = 10.0`).
- **`script = ExtResource("...")`** attaches a script. A script is always an `ext_resource`, never a
  `SubResource`.
- **Instance another scene** with `instance=` and **no `type`**:
  `[node name="Coin1" parent="." instance=ExtResource("2_coin")]`, then override properties
  below it (`position = Vector2(200, 120)`).
- **Groups** go on the node line: `groups=["coins"]`. A node can be in several:
  `groups=["enemies", "damageable"]`.
- **Unique names:** `unique_name_in_owner = true` as a property line under the node. Scripts in
  that scene then reach it as `%Score` from anywhere in the scene, and moving the node doesn't break
  the reference.

### What *not* to write

| Don't write | Why |
| --- | --- |
| `load_steps=N` in the header | Since 4.6 Godot doesn't write it and ignores it if present. A wrong count used to break loading, so leaving it out is safest |
| `uid="uid://..."` on the header or an `ext_resource` | Optional. Godot resolves by `path`. An invented uid that matches nothing gives a warning, or worse, resolves to the wrong file |
| `unique_id=...` on nodes | Godot 4.6+ adds these itself when it saves a scene, to track renames. Scenes without them load fine |
| `[connection]` entries | This project connects signals in `_ready()` |
| Editor-only metadata (`metadata/_edit_lock_`, `editor_description`) | Noise in diffs |

When Godot resaves a hand-written scene, the editor or an MCP `save_scene` call may add `uid=` and
`unique_id=` and rename ids (`"1_coin"` → `"1_usft0"`). That is normal. Commit what Godot wrote;
don't fight it.

---

## 2. One scene per thing

Every kind of thing gets **one scene and one script with the same name**:

```
scenes/main.tscn     scripts/main.gd       the game: arena, player, and whatever main spawns
scenes/player.tscn   scripts/player.gd     the player body
scenes/coin.tscn     scripts/coin.gd       one coin (main instances or spawns several)
scenes/hud.tscn      scripts/hud.gd        score and health display
```

- `main.tscn` is the **composition** scene. It instances other scenes and holds level layout
  (walls, background), and nothing that belongs to one kind of thing.
- Many instances of one thing (coins, enemies) are **spawned from `main.gd`** with a preloaded scene,
  or listed as instance nodes in `main.tscn` when their positions are fixed. Either way, the scene
  root carries the group (`coins`), so tests and the playtester can count them.
- A scene root's script should not reach into another scene's children. Talk through signals,
  groups or `GameState`.

### Node names and depth

- Node names are `PascalCase` (`Player`, `Walls`, `HUD`, `Score`). Nodes of the same kind that
  you'll address in a group get numbered names (`Coin1`, `Coin2`), or any names if they're spawned.
- **Keep trees shallow.** A path that needs more than one `/` (`$A/B/C`) is a sign to make the
  inner part its own scene or to use `%UniqueName`. Group several same-kind siblings under a plain
  `Node2D` container (`Coins`) if `main.tscn` gets crowded.

---

## 3. This project's scenes

| Scene | Root | Notes |
| --- | --- | --- |
| `main.tscn` | `Main` (Node2D, `scripts/main.gd`) | `Background` (ColorRect), `Walls` (StaticBody2D: four `CollisionShape2D` edges plus `ColorRect` visuals, 32 px thick), `Player` (instance) at (480, 270) |
| `player.tscn` | `Player` (CharacterBody2D, group `player`, `motion_mode = 1` floating) | `Body` (Polygon2D, 32×32), `Collision` (CircleShape2D r=16) |

- **Viewport** 960×540, stretch mode `canvas_items`. The arena interior runs from (32, 32) to
  (928, 508).
- **No image assets.** Shapes are `Polygon2D` or `ColorRect`. A feature that needs art uses those
  too, unless it says otherwise.
- **HUD** goes in a `CanvasLayer` named `HUD` with `Label` children, so it stays put if a camera is
  added later. Give labels a `mouse_filter = 2` (ignore) if they overlap the play area.
- **Collision:** an `Area2D` detects the player through `body_entered` (the player is a physics
  body). The default layer and mask (layer 1) are fine unless a feature needs otherwise.
- **Renderer** is `gl_compatibility`, so it works on any machine and in the MCP-driven playtest.

### A HUD scene

```ini
[gd_scene format=3]

[ext_resource type="Script" path="res://scripts/hud.gd" id="1_hud"]

[node name="HUD" type="CanvasLayer"]
script = ExtResource("1_hud")

[node name="Score" type="Label" parent="."]
unique_name_in_owner = true
offset_left = 44.0
offset_top = 40.0
offset_right = 244.0
offset_bottom = 66.0
mouse_filter = 2
text = "Score: 0"
```

And instanced into `main.tscn`, after the existing resources:

```ini
[ext_resource type="PackedScene" path="res://scenes/hud.tscn" id="3_hud"]

...

[node name="HUD" parent="." instance=ExtResource("3_hud")]
```

---

## 4. Editing a scene by hand

1. **Read the whole file first.** Find the highest numbered id and the exact parent names.
2. Add any `[ext_resource]` lines after the existing ones, and any `[sub_resource]` blocks after
   those. **Never** put a resource after the first `[node]`.
3. Add `[node]` blocks after their parent's block.
4. Run `bin/check.sh` (or at least
   `bin/godot --headless --path . --import`) and read every `ERROR:` line.

**Good to hand-edit:** adding nodes, instancing scenes, setting properties, groups, collision
shapes, labels, simple Polygon2D / ColorRect visuals.

**Generate rather than hand-write:** `TileMapLayer` tile data (a packed binary array),
`AnimationPlayer` libraries with many tracks, `AnimationTree` graphs, anything a designer will tweak
visually. For those, build the scene from a headless script (`PackedScene.pack()` +
`ResourceSaver.save()`) or the MCP scene tools (`create_scene`, `add_node`, `save_scene`). Then the
engine writes the format.

### What Godot says when a scene is wrong

These are real 4.7.2 messages, produced by breaking `player.tscn` on purpose:

| Mistake | What Godot prints | Does the gate fail? |
| --- | --- | --- |
| `SubResource("id")` with an id that isn't defined, or a resource placed after the first `[node]` | `Condition "!int_resources.has(id)" is true` then `Parse Error: Invalid parameter. [Resource file res://scenes/player.tscn:17]` | Yes |
| `path=` points at a missing file | `[ext_resource] referenced non-existent resource at: res://scripts/playr.gd` | Yes |
| Stray character on a property line (`radius = 16.0)`) | Errors that make no sense (`root node Body cannot specify a parent node`, a script assigned to the wrong object): the parser lost track of where it was | Yes |
| **`parent=` names a node that doesn't exist** | `WARNING: Parent path './Nope' for node 'Body' has vanished when instantiating` | **No.** The node is silently dropped |
| **`type=` left off a non-instance node** | `WARNING: Node './Body' was modified from inside an instance, but it has vanished.` | **No.** The node is silently dropped |
| Two siblings with the same name | Nothing obvious; Godot renames one. The only sign is leak noise at exit | Only by accident |

Read **warnings** as well as errors after touching a scene: `bin/check.sh` fails only on
`ERROR`, `SCRIPT ERROR` and `Parse Error` lines. Scene mistakes that silently drop a node show up
as a `WARNING: ... vanished` line, and later as a test that can't find the node. When the first
error makes no sense, look at the line it names and the line just above it.

Path case matters: macOS is case-insensitive, Linux CI isn't. `res://Scenes/Coin.tscn` loads on a
Mac and fails in CI.

---

## 5. `.uid` files and moving things

- Since Godot 4.4, each script has a **`.gd.uid` sidecar** (`player.gd.uid`, one line:
  `uid://...`). The import step creates it for a new script. **Commit it with the script.**
- Moving or renaming a script means moving or renaming its `.uid` too (`git mv` both). Otherwise
  anything that referenced it by uid breaks.
- Scenes and resources store their uid inside the file's header, so they have no sidecar.
- `.godot/` is the import cache. It's ignored by git; never edit it. Deleting it is safe (the next
  `--import` rebuilds it) and fixes "class not found" errors from a stale cache.

---

## 6. Spawning from code instead

When counts or positions are computed (five coins at random spots, enemies over time), spawn from
the script rather than listing nodes in the `.tscn`:

```gdscript
extends Node2D
## Root of the game scene. Spawns the coins.

const CoinScene := preload("res://scenes/coin.tscn")
const COIN_COUNT := 5


func _ready() -> void:
	GameState.reset()
	for i in COIN_COUNT:
		var coin := CoinScene.instantiate() as Node2D
		coin.position = Vector2(160 + i * 160, 140)
		add_child(coin)
```

The coin scene's root already carries `groups=["coins"]`, so every spawned coin is in the group.
See [PATTERNS.md](PATTERNS.md) for random placement that keeps clear of walls and the player.
