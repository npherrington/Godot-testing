extends "res://tests/test_case.gd"
## The generated assets (art/build.py, art/audio/build_audio.py) load in Godot and have what
## assets_spec.md asks for: directions, frame counts, states, the tileset, fonts and sounds.

const PLAYER_STATES: Array[String] = ["normal", "injured", "frozen", "poisoned"]
const DIRECTIONS_8: Array[String] = [
	"down", "down_right", "right", "up_right", "up", "up_left", "left", "down_left"
]
const DIRECTIONS_4: Array[String] = ["down", "up", "left", "right"]
const MONSTERS: Array[String] = [
	"skeleton_warrior",
	"ghost",
	"goblin",
	"slime",
	"spider",
	"ogre",
	"dark_mage",
	"zombie",
	"harpy",
	"mimic",
	"basilisk",
	"wolfman",
	"imp",
	"medusa",
	"goblin_king",
	"ice_elemental",
	"hellhound",
	"vampire",
	"troll",
	"lich",
]
const SOUND_PREFIXES: Array[String] = [
	"sfx_player_footstep",
	"sfx_player_attack",
	"sfx_player_pickup",
	"sfx_combat_swing",
	"sfx_combat_spell",
	"sfx_combat_hit",
	"sfx_combat_miss",
	"sfx_enemy_growl",
	"sfx_enemy_screech",
	"sfx_enemy_death",
	"sfx_environment_torch",
	"sfx_environment_ambience",
	"sfx_ui_move",
	"sfx_ui_click",
	"music_main",
	"music_battle",
	"music_boss",
	"music_victory",
	"music_ambient",
]


func _sprite_frames(path: String) -> SpriteFrames:
	if not ResourceLoader.exists(path):
		check(false, "%s is missing" % path)
		return null
	var frames := load(path) as SpriteFrames
	check(frames != null, "%s should load as SpriteFrames" % path)
	return frames


func _check_counts(
	frames: SpriteFrames, label: String, animation: String, low: int, high: int
) -> void:
	if not frames.has_animation(animation):
		check(false, "%s has no %s" % [label, animation])
		return
	var count := frames.get_frame_count(animation)
	check(count >= low and count <= high, "%s %s: %d frames" % [label, animation, count])


func _files(folder: String, extension: String) -> Array[String]:
	var found: Array[String] = []
	for file: String in DirAccess.get_files_at(folder):
		if file.get_extension() == extension:
			found.append(folder.path_join(file))
	return found


func test_player_has_8_directions_and_the_spec_frame_counts_in_all_4_states() -> void:
	var counts := {"idle": 4, "walk": 8, "attack": 6, "defend": 2}
	for state: String in PLAYER_STATES:
		var frames := _sprite_frames("res://assets/sprites/player/char_player_%s.tres" % state)
		if frames == null:
			continue
		for animation: String in counts:
			var count: int = counts[animation]
			for direction: String in DIRECTIONS_8:
				_check_counts(frames, state, "%s_%s" % [animation, direction], count, count)


func test_all_20_monsters_have_4_directions_and_the_spec_animations() -> void:
	for monster: String in MONSTERS:
		var frames := _sprite_frames("res://assets/sprites/enemies/char_%s_normal.tres" % monster)
		if frames == null:
			continue
		for direction: String in DIRECTIONS_4:
			_check_counts(frames, monster, "idle_" + direction, 4, 4)
			_check_counts(frames, monster, "walk_" + direction, 8, 8)
			_check_counts(frames, monster, "attack_" + direction, 1, 12)
			_check_counts(frames, monster, "special_" + direction, 2, 12)
			_check_counts(frames, monster, "death_" + direction, 4, 6)
			if frames.has_animation("death_" + direction):
				check(
					not frames.get_animation_loop("death_" + direction),
					"%s death_%s should not loop" % [monster, direction]
				)


func test_every_sprite_frames_resource_loads_with_textures() -> void:
	var total := 0
	for folder: String in ["player", "enemies", "environment", "ui"]:
		for path: String in _files("res://assets/sprites/" + folder, "tres"):
			var frames := _sprite_frames(path)
			if frames == null:
				continue
			for animation: String in frames.get_animation_names():
				check(frames.get_frame_count(animation) > 0, "%s %s is empty" % [path, animation])
				check(
					frames.get_frame_texture(animation, 0) != null,
					"%s %s has no texture" % [path, animation]
				)
			total += 1
	check(total > 40, "only %d SpriteFrames resources found" % total)


func test_tileset_has_the_atlas_tiles_and_wall_collision() -> void:
	var tileset := load("res://assets/tilesets/tileset_dungeon.tres") as TileSet
	check(tileset != null, "tileset_dungeon.tres should load as a TileSet")
	if tileset == null:
		return
	check_eq(tileset.tile_size, Vector2i(16, 16), "tile size")
	check(tileset.get_physics_layers_count() > 0, "the tileset needs a physics layer for walls")
	var source := tileset.get_source(tileset.get_source_id(0)) as TileSetAtlasSource
	check(source != null, "the tileset's first source should be an atlas")
	if source != null:
		check(source.get_tiles_count() >= 8 + 12, "8 floors and 12 walls at least")


func test_both_fonts_load_with_the_printable_ascii_glyphs() -> void:
	for path: String in [
		"res://assets/fonts/font_dungeon.fnt", "res://assets/fonts/font_dungeon_outline.fnt"
	]:
		var font := load(path) as FontFile
		check(font != null, "%s should load as a FontFile" % path)
		if font != null:
			check(font.get_height(16) > 0.0, "%s has no height" % path)
			check(font.has_char("g".unicode_at(0)), "%s has no g" % path)
			check(font.has_char("~".unicode_at(0)), "%s has no ~" % path)


func test_every_sound_loads_and_each_spec_category_has_one() -> void:
	var names: Array[String] = []
	for folder: String in ["res://assets/sounds/sfx", "res://assets/sounds/music"]:
		for path: String in _files(folder, "ogg"):
			var stream := load(path) as AudioStream
			check(stream != null, "%s should load as an AudioStream" % path)
			if stream != null:
				check(stream.get_length() > 0.0, "%s is empty" % path)
			names.append(path.get_file())
	for prefix: String in SOUND_PREFIXES:
		check(
			names.any(func(n: String) -> bool: return n.begins_with(prefix)), "no %s sound" % prefix
		)
