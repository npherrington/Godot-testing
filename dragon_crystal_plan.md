# Dragon Crystal Remake - Build Plan

## Asset Requirements
See [assets_spec.md](assets_spec.md) for detailed asset specifications including sprite requirements, monster types, environmental assets, and sound design.

## Art Delivery Plan
Assets should be delivered in stages matching development phases:
1. Phase 1: Player character, basic tilesets, core UI
2. Phase 2: First 5 enemy types, traps, environmental effects
3. Phase 3: Remaining enemy types, sound effects
4. Phase 4: Music tracks, additional decorations
5. Phase 5: Final polish assets

## Overview
Modernized remake of Dragon Crystal inspired by Halls of Torment's monster variety and aesthetic.

## Build Plan - Staged Approach

### Phase 1: Core Infrastructure
**Goal**: Establish the foundational systems

- Feature 1: Godot Project Setup (See [features/0001-godot-project-setup.md](features/0001-godot-project-setup.md))
  - Initialize Godot 4.7 project
  - Configure input actions
  - Set up basic scene structure

- Feature 2: Player Character System (See [features/0002-player-character.md](features/0002-player-character.md))
  - Create player sprite and animation controller
  - Implement grid-based movement
  - Add basic collision detection

- Feature 3: Dungeon Framework (See [features/0003-dungeon-framework.md](features/0003-dungeon-framework.md))
  - Create tilemap system
  - Implement simple room generation
  - Add wall/collision logic

### Phase 2: Combat System
**Goal**: Implement turn-based combat mechanics

- Feature 4: Enemy AI Framework (See [features/0004-enemy-ai-framework.md](features/0004-enemy-ai-framework.md))
  - Create basic enemy template
  - Implement turn-based movement
  - Add simple attack logic

- Feature 5: Combat Manager (See [features/0005-combat-manager.md](features/0005-combat-manager.md))
  - Create turn system controller
  - Implement action queue
  - Add status effect framework

### Phase 3: Content Systems
**Goal**: Add game content and variety

- Feature 6: Monster Database (See [features/0006-monster-database.md](features/0006-monster-database.md))
  - Create 10 monster types with unique sprites
  - Implement unique behaviors
  - Add health/damage stats

- Feature 7: Item System (See [features/0007-item-system.md](features/0007-item-system.md))
  - Create inventory framework
  - Implement weapon/armor stats
  - Add consumable items

### Phase 4: Dungeon Experience
**Goal**: Enhance dungeon crawling features

- Feature 8: Trap System (See [features/0008-trap-system.md](features/0008-trap-system.md))
  - Create trap templates
  - Implement activation logic
  - Add visual effects

- Feature 9: Lighting & Atmosphere (See [features/0009-lighting-atmosphere.md](features/0009-lighting-atmosphere.md))
  - Add torch lighting system
  - Implement fog of war
  - Add ambient sounds

### Phase 5: Polish & Systems
**Goal**: Complete game systems

- Feature 10: Save/Load System (See [features/0010-save-load-system.md](features/0010-save-load-system.md))
  - Implement game state serialization
  - Add checkpoint system
  - Create menu UI

- Feature 11: UI & HUD (See [features/0011-ui-hud.md](features/0011-ui-hud.md))
  - Create health display
  - Add turn indicator
  - Implement inventory screen

## Execution Strategy

1. Start with Phase 1 (3 features)
2. Validate core movement and dungeon mechanics
3. Move to Phase 2 (2 features)
4. Implement combat system
5. Proceed to Phase 3 (2 features)
6. Build monster variety and items
7. Continue to Phase 4 (2 features)
8. Enhance atmosphere and traps
9. Complete with Phase 5 (2 features)
10. Polish and testing

Each phase creates testable milestones. Features should be:
- Small enough to complete in 1-2 days
- Focused on specific functionality
- Testable in isolation
- Build upon previous features
