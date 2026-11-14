# Dragon Crystal Remake - Asset Specification

## Overview
Asset requirements for the modernized Dragon Crystal remake with Halls of Torment influences.

## Core Requirements

### Visual Style
- **Pixel Art Resolution**: 16x16 pixels per tile
- **Color Palette**: Limited to 24 colors to maintain pixel art aesthetic
- **Lighting**: Torch-like lighting effects for dungeon atmosphere
- **Transparency**: Support for semi-transparent elements (smoke, fog)

### Character Sprites

#### Player Character
- **Base Sprite**: 32x48 pixels (2 tiles tall)
- **Animations**: 
  - Idle (4 frames)
  - Walk (8 frames)
  - Attack (6 frames)
  - Defend (2 frames)
- **States**: Normal, injured, frozen, poisoned

#### Enemy Monsters (20 types required)
**Size**: 32x48 or 48x48 pixels
**Animation Requirements for each**:
- Idle (4 frames)
- Walk (8 frames)
- Attack (1-2 attack animations per enemy)
- Special ability (unique to monster type)
- Death (4-6 frames)

**Monster Types & Behaviors**:
1. Skeleton Warrior - Melee fighter
2. Ghost - Float through walls
3. Goblin - Throw rocks
4. Slime - Split when hit
5. Spider - Web trap
6. Ogre - Heavy damage
7. Dark Mage - Caster
8. Zombie - Slow shambling
9. Harpy - Flying attacker
10. Mimic - Disguised as treasure
11. Basiltisk - Petrifying gaze
12. Wolfman - Pack tactics
13. Imp - Fireball caster
14. Medusa - Stares turn to stone
15. Goblin King - Elite fighter
16. Ice Elemental - Freezes player
17. Hellhound - Fire breath
18. Vampire - Life drain
19. Troll - Regenerates health
20. Lich - Ultimate boss

### Environment Assets

#### Tilesets
- **Floor Tiles**: 8 variations (stone, dirt, lava, etc.)
- **Wall Tiles**: 12 variations (stone, cracked, ruined)
- **Decorations**: 20+ objects (pillars, torches, bones, furniture)
- **Special Tiles**: Traps, doors, stairs, secret passages

#### Dungeon Props
- **Torches**: Animated flickering (4 frames)
- **Chests**: Closed, opened, trapped variants
- **Doors**: Wooden, metal, magical
- **Stairs**: Downward, upward
- **Traps**: Pressure plates, spike walls, arrow traps
- **Environment Effects**: Fire, smoke, blood splatters

### UI Elements
- **Health Bar**: Red/white gradient with damage animation
- **Inventory Slots**: 24 slots with highlight effects
- **Action Buttons**: Turn-based command interface
- **Menu Background**: Dungeon wall texture
- **Status Icons**: Poison, freeze, burn indicators
- **Font**: Pixel-style font for all text

### Sound Effects
- **Character Actions**: Footsteps, attack swings, item pickups
- **Combat**: Weapon swings, spell casts, hits, misses
- **Enemies**: Growls, screeches, death screams
- **Environment**: Torch crackling, dungeon ambience
- **UI**: Menu navigation, button clicks

### Music
- **Main Theme**: Dungeon crawling background music
- **Battle Music**: Intensified combat theme
- **Boss Theme**: Unique battle music for bosses
- **Victory Music**: Short celebration tune
- **Ambient Loops**: Dungeon atmosphere variations

## Technical Specifications

### File Formats
- **Sprites & Tiles**: PNG with transparency
- **UI Elements**: PNG with transparency
- **Audio**: OGG format for compression
- **Music**: OGG format
- **Font**: BMFont or similar pixel font format

### Naming Convention
- **Sprites**: `char_[name]_[state]_[frame].png`
- **Tiles**: `tile_[type]_[variant].png`
- **Decorations**: `decor_[type]_[variant].png`
- **Traps**: `trap_[type]_[state].png`
- **UI**: `ui_[component]_[state].png`
- **Sound FX**: `sfx_[category]_[action].ogg`
- **Music**: `music_[theme]_[variant].ogg`

## Animation Guidelines

### Frame Rates
- **Player/Enemies**: 8-10 FPS
- **Environment**: 4-6 FPS
- **UI**: 12 FPS

### Directions
- **Player**: 8-directional movement
- **Enemies**: 4-directional (front/back/left/right)

### Pixel Art Standards
- **Anti-aliasing**: Avoid on hard edges
- **Dithering**: Use for smooth transitions
- **Shading**: 2-3 tint shades per color
- **Silhouettes**: Distinct shapes for each monster

## Delivery Structure

```
assets/
├── sprites/
│   ├── player/
│   ├── enemies/
│   ├── environment/
│   └── ui/
├── tilesets/
├── sounds/
│   ├── sfx/
│   └── music/
├── fonts/
└── animations/
    ├── player.json
    ├── enemies/
    └── environment.json
```

## Development Notes

1. **Progression**: Deliver assets in batches matching game development phases
2. **Testing**: Provide test versions with color palette limited to design constraints
3. **Iteration**: Expect 2-3 revision cycles per asset type
4. **Documentation**: Include readme with asset usage notes
5. **Licensing**: Ensure all assets are original or properly licensed

## Priority Order

1. Player character (highest priority)
2. Core 5 enemy types
3. Basic tilesets
4. UI elements
5. Remaining enemies
6. Traps and special tiles
7. Environmental effects
8. Sound effects
9. Music tracks
10. Additional decorations

## Testing Requirements

- All sprites must test in-game with proper lighting
- Animations must loop smoothly
- Transparency must render correctly
- Sound effects must sync with visuals
- UI elements must be readable at 1920x1080
