---
description: Build a feature file end to end in this session (plan, implement, gate, playtest, review)
---

Build the feature in $ARGUMENTS, attended: I am here, so ask when something is genuinely unclear.

1. Use the planner subagent to write runs/<feature name>/plan.md from the feature file. Show me
   the plan's Decisions section and wait for my go-ahead.
2. Implement the plan yourself following the implementer agent's steps, until bin/check.sh passes.
3. Use the playtester subagent to check every acceptance criterion in the running game. If it
   fails, fix and repeat.
4. Use the reviewer subagent to review the change. Make the required changes, rerun bin/check.sh.
5. Summarise what was built, the tests added and the playtest evidence. Do not commit.
