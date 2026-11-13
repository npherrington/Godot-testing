---
name: godot-scenes
description: How to write and edit Godot 4 .tscn scene files by hand safely, and the scene layout of this project. Load before creating or changing any .tscn file.
---

# Scenes (.tscn)

Scenes here are written as text. Godot is strict about the format; a bad scene fails the gate's
`import` or `scenes` step. Read the whole scene file before editing it.

A `parent=` that names a missing node, or a node without `type=` (and not an `instance=`), makes
Godot drop the node with a `WARNING: ... has vanished`. The gate fails on that line; fix the
`parent`/`type` it names.

## Format

```
[gd_scene format=3]

[ext_resource type="Script" path="res://scripts/coin.gd" id="1_coin"]
[ext_resource type="PackedScene" path="res://scenes/coin.tscn" id="2_coin"]

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

Order: the `[gd_scene]` header, then every `[ext_resource]`, then every `[sub_resource]`, then the
`[node]` entries. Each section is followed by a blank line.

- **ids are unique within a file**, and every `ExtResource("id")` / `SubResource("id")` names an id
  defined above it. Use readable ids (`"1_coin"`, `"CircleShape2D_coin"`).
- **The first `[node]` is the root** and has no `parent`. Its direct children use `parent="."`;
  grandchildren use the child's name (`parent="Walls"`), deeper ones a path (`parent="Walls/Top"`).
- **Instancing another scene**: `[node name="Coin1" parent="." instance=ExtResource("2_coin")]`,
  no `type`. Set `position = Vector2(...)` under it.
- **Groups** go on the node line: `groups=["coins"]`.
- Do not write `uid=` attributes or `load_steps`; Godot does not need them.
- Values are Godot literals: `Vector2(1, 2)`, `Color(r, g, b, a)` from 0 to 1, floats with `.0`.

## This project

- `main.tscn`: `Main` (Node2D, scripts/main.gd), `Background`, `Walls` (StaticBody2D with the four
  edge collisions, 32 px thick, arena interior from (32, 32) to (928, 508)), `Player` (instance).
- `player.tscn`: `Player` (CharacterBody2D, group `player`, 32x32 square, circle collision r=16).
- The viewport is 960x540. Shapes are drawn with `Polygon2D` or `ColorRect`; there are no image
  assets. A HUD goes in a `CanvasLayer` named `HUD` with `Label` children.
- A new kind of thing gets its own scene and script (`scenes/coin.tscn` + `scripts/coin.gd`) and is
  instanced into `main.tscn` or spawned from `main.gd`.
- **Collision**: an `Area2D` detects the player with `body_entered` (the player is a physics body).
  Default collision layers and masks are fine unless the feature needs otherwise.
