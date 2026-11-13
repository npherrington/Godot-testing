---
description: Build a feature file step by step in this session (plan, build, gate, playtest, self-review)
---

Build the feature in $ARGUMENTS, following "Building a feature" in AGENTS.md. Do one step at a
time and stop where it says to stop.

1. Load the feature-plan skill. Write runs/<feature name>/plan.md. Show me its Decisions section
   and **stop until I say go**.
2. Build what the plan lists, tests included.
3. Run bin/check.sh. Fix the first failure, rerun, repeat until every step is ok. After 3 failed
   attempts on the same failure, stop and tell me what you tried.
4. Load the godot-playtest skill. Check every acceptance criterion in the running game and write
   runs/<feature name>/playtest.md. Fix and repeat from step 3 if anything fails.
5. Self-review `git diff` against the feature file and AGENTS.md rules 1 to 6. Fix what you find
   and rerun bin/check.sh.
6. Summarise what was built, the tests added and the playtest evidence. Do not commit.
