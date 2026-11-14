# Save/Load System

Implement game state serialization and checkpoint system.

## Acceptance criteria

1. Game state serialization (snapshot method)
2. Save to file system
3. Load from saved state
4. Checkpoint system in dungeon
5. Menu UI for save/load

## Out of scope

- Auto-save functionality
- Cloud saving
- Save slots beyond basic
- Version migration

## Notes

- Save format: JSON
- Checkpoints appear as special tiles
- Menu accessible from pause
- Snapshot includes player position, health, inventory, enemies
- Load maintains turn order