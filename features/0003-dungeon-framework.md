# Dungeon Framework

Implement the basic dungeon tilemap system and room generation.

## Acceptance criteria

1. Tilemap system creates basic arena with floor and walls
2. Simple room generation produces 3x3 tile room
3. Wall collision blocks player movement
4. Dungeon scene can be loaded as part of main scene
5. Arena boundaries prevent player from leaving grid

## Out of scope

- Multiple rooms or dungeon levels
- Decorations or traps
- Enemy spawning logic
- Lighting effects

## Notes

- Tile size: 16x16 pixels
- Arena dimensions: 32x32 tiles minimum
- Walls should be solid collision
- Floor tiles should allow movement
- Room generation should be deterministic for testing