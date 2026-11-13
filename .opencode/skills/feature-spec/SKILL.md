---
name: feature-spec
description: Write or improve a feature file in features/ so it can be built end to end with /feature. Use when the user describes a feature to build, or asks to write or check a feature file.
---

# Feature file

A feature file is the input to `/feature`. It says **what** the player gets and how to tell it
works. It does not say how to build it; that is decided later, in the plan.

Name it `features/NNNN-short-name.md`, numbered after the highest existing file.

```markdown
# Coins and score

Five coins sit around the arena. Walking into one collects it and adds to a score shown on screen.

## Acceptance criteria

1. When the game starts there are 5 coins in the arena, none touching a wall or the player.
2. Walking the player into a coin removes that coin and adds 10 to the score.
3. The score is shown top-left as "Score: N" and updates when a coin is collected.
4. A collected coin cannot be collected again.

## Out of scope

- Coins respawning, sounds, animations.

## Notes

- Coins are gold squares, smaller than the player.
```

## What makes criteria buildable

- **Observable**: each one names something a test or a playtest can check (a number in
  `GameState`, a node count, text on screen), not a feeling ("feels responsive").
- **Specific**: exact numbers and text ("adds 10", "Score: N"), not "some points".
- **One behaviour each**, three to six per file. A bigger feature becomes several files built in order.
- **Out of scope** stops gold-plating. Notes hold hints (look, placement) that are
  not requirements.
