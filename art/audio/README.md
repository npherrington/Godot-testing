# Audio

Every sound and track here is original, made from scratch by a small stdlib-only
Python synth (`dsp.py`, `music.py`). Nothing is sampled or copied.

## Rebuild

```sh
python3 art/audio/build_audio.py                    # everything, about 1 minute
python3 art/audio/build_audio.py --only sfx_ui_click  # one file (globs work: 'sfx_enemy_*')
python3 art/audio/build_audio.py --list             # names
python3 art/audio/verify_audio.py                   # measure all files, exit 1 on a problem
```

- Needs Python 3 (stdlib only) and `ffmpeg` (its native Vorbis encoder is enough).
- All randomness is seeded, so a rebuild produces byte-identical `.ogg` files.
- The intermediate 16-bit WAVs go to `art/out/audio/`, which is gitignored.
- Sources:
  - `sfx.py`: the sound effects.
  - `tracks.py`: the music, written in a small note notation.
  - `music.py`: the sequencer and instruments.
- `--levels` prints each music part's loudness, which is how the mixes were balanced.

## Looping in Godot

Godot only loops an OGG when code sets `loop = true`. The `.import` files are
gitignored, so set it where the stream is used:

```gdscript
var stream := load("res://assets/sounds/music/music_main_loop.ogg") as AudioStreamOggVorbis
stream.loop = true
```

Loop the files marked **loop** below, and no others.
- Each loop is rendered to an exact length, a multiple of 64 samples, so the Ogg end
  position is sample-exact and the loop is gapless.
- Note tails, echoes and reverb wrap around from the end into the start.
- Each loop starts on a near-silent sample. A short volume fade-in on first play,
  or a crossfade between tracks, is still the smoothest way to start one.

## Levels

- One-shot SFX peak at -1 dBFS, and their loudest moment is capped near -11 LUFS
  so they sit together. Footsteps (about -20) and UI sounds (-15 to -22) are
  deliberately quieter.
- Music is about -15 LUFS and the ambient tracks about -16, with peaks at or below
  -1 dBFS.
- The two environment loops are beds at about -22 LUFS.

## Sound effects: `assets/sounds/sfx/`

| File | Length | What it is, and when it plays |
| --- | --- | --- |
| `sfx_player_footstep_1` .. `_4` | 0.3 s | Boot on stone. Play one at random per step taken. |
| `sfx_player_attack_1`, `_2` | 0.5-0.6 s | Player sword slash with blade ring, on the player's attack animation. |
| `sfx_player_pickup_1` | 0.5 s | Three-note blip, on picking up an ordinary item. |
| `sfx_player_pickup_2` | 0.6 s | Rising major arpeggio with shimmer, for rare items or treasure. |
| `sfx_combat_swing_1` .. `_3` | 0.2-0.5 s | Weapon whoosh for any combatant: light blade, sword, heavy axe or club. |
| `sfx_combat_spell_fire` | 1.3 s | Fire cast: ignition whump, roar and crackle. Fireballs, fire breath. |
| `sfx_combat_spell_ice` | 1.3 s | Ice cast: frost hiss, crystal glints and a cracking tink. Freeze attacks. |
| `sfx_combat_spell_dark` | 2.0 s | Dark cast: falling detuned drone, inhaled rush and sub boom. Life drain, curses. |
| `sfx_combat_spell_arcane` | 1.4 s | Arcane cast: rising FM sweep, arpeggio and chime. Generic magic. |
| `sfx_combat_hit_1` | 0.4 s | Body thud: a hit on flesh or cloth. |
| `sfx_combat_hit_2` | 0.5 s | Armour clank: a hit on metal, bone armour or a shield. |
| `sfx_combat_hit_3` | 0.4 s | Heavy bone-crunching hit: critical hits and big monsters. |
| `sfx_combat_miss` | 0.2 s | Airy whiff, when an attack misses. |
| `sfx_enemy_growl_1` | 1.2 s | Deep beast growl: ogre, troll, wolfman. Plays on alert or aggro. |
| `sfx_enemy_growl_2` | 1.0 s | Mid growl: goblin, zombie, skeleton. |
| `sfx_enemy_growl_3` | 0.8 s | Small snarl: imp, hellhound, spider. |
| `sfx_enemy_screech_1` | 1.0 s | Harpy cry: flyers attacking. |
| `sfx_enemy_screech_2` | 0.8 s | Chittering: spiders, bats, small vermin. |
| `sfx_enemy_screech_3` | 2.0 s | Ghostly wail: ghost, lich, vampire. |
| `sfx_enemy_death_1` | 1.8 s | Large beast death with a body-fall thud. |
| `sfx_enemy_death_2` | 1.2 s | Humanoid death cry: goblins, wolfman, cultists. |
| `sfx_enemy_death_3` | 1.7 s | Small or spectral death dissolving into hiss: imp, ghost, slime. |
| `sfx_environment_torch_loop` | 5.0 s | **Loop.** Flame roar with crackles and pops. Attach to torch props. |
| `sfx_environment_ambience_loop` | 30.0 s | **Loop.** Low drone, moving air, faint wind and distant drips. Plays under each dungeon floor. |
| `sfx_ui_move` | 0.05 s | Menu cursor tick, when the selection moves. |
| `sfx_ui_click` | 0.05 s | Button press. |
| `sfx_ui_confirm` | 0.4 s | Rising two-note confirm: accept, equip, start. |
| `sfx_ui_cancel` | 0.3 s | Falling two-note cancel: back, close. |

To give each of the 20 monster types its own voice from these 3 variants, set
`pitch_scale` per monster, for example 0.8 for big ones and 1.25 for small ones.

## Music: `assets/sounds/music/`

| File | Length | What it is, and when it plays |
| --- | --- | --- |
| `music_main_loop` | 62.6 s | **Loop.** Exploration theme in D minor, 92 BPM. Plays while crawling a floor. |
| `music_battle_loop` | 50.5 s | **Loop.** The exploration motif made faster and harder, D minor, 152 BPM. Plays in combat. |
| `music_boss_loop` | 58.2 s | **Loop.** E Phrygian with 3+3+2 drums, brass, choir and bells, 132 BPM. Boss fights such as the Lich or the Goblin King. |
| `music_victory_fanfare` | 5.6 s | No loop. Bb-C-D major cadence, played once after a battle is won. |
| `music_ambient_crypt` | 60.0 s | **Loop.** Sparse D minor pads and a glass-bell melody. Quiet floors, crypts, safe rooms. |
| `music_ambient_caverns` | 48.0 s | **Loop.** Dark pad and drone with echoing plucks like drips. Caves and deeper floors. |
| `music_ambient_depths` | 51.4 s | **Loop.** C# Phrygian drone, choir and distant church bell. Lowest floors, before a boss. |
