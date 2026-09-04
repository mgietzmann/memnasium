---
name: wordsmithing
description: Cut memnasium placements into recall pairs — the short question/answer pairs that are actually drilled. Use when the user says there are placements waiting for pairs, mentions stale pairs, or wants to work the wordsmithing queue. Requires `make run` to be up.
---

# Wordsmithing

Built from `design/flows/Wordsmithing.md`. Read that doc if anything here is
unclear.

## The pass

1. `list_pending_placements` — placements with **no live pairs** (newly placed) or
   with `pairs_stale = 1` (moved, so their pairs were written for the wrong
   siblings). Each one already carries everything you read:

   | Input | Why |
   |---|---|
   | the note's statement | the material |
   | the group's other notes | whether this fact is genuinely distinct |
   | the group's existing pairs | what is already asked, and what could be eliminated |

   A full queue can exceed the tool result limit and land in a file instead.
   Read it by group with `jq` rather than dumping the whole thing — one group per
   pass is the working unit anyway.

2. Propose pairs, one pass of notes at a time.
3. The user strikes or corrects what is wrong. Everything else is written.
4. `write_pairs` — the placement's **whole set** in one call. It clears the stale
   flag for you.

## What makes a pair

- **One answer, one pair.** Two numbers that are genuinely two facts are two
  pairs. A list that only means anything whole is one pair whose answer is the
  list — asking for one of three would be a different, easier question.
- **Specific enough to be unambiguous in its group.** "At what length?" is broken
  on a board of five length thresholds.
- **Self-contained.** Pairs drill in isolation and in random order. No question
  may borrow its subject from a sibling — "and by September?" is broken. Name
  the region, the stage, the river, every time.
- **Subject first.** Bury the interrogative rather than opening on it. Not "At
  what length do Yukon River Chinook transition to piscivory?" — "Yukon River
  Chinook become piscivorous at what length?" Shorter, and the thing being
  recalled leads.
- **Not answerable by elimination.** Sibling answers are visible on the board. A
  question solvable by reading them tests reading, not recall.
- **Short.** One line of question, one line of answer, wherever the fact allows. A
  long answer is a signal the pair holds more than one fact.
- **LaTeX is preserved** from the note and rendered on the board.
- **The source is never in the pair.** It is asked as its own box at drill time.

Roll placements are in the queue too. Their pairs have no context to be worded
against, which makes them the ones most in need of being self-contained.

## Writing the set

`write_pairs` takes the placement's whole set. The shape says what happens:

| Entry | Means |
|---|---|
| has `id` | reword that pair; `sessions_correct` untouched |
| no `id`, no `inherit_from` | a new pair at `sessions_correct = 0` |
| no `id`, with `inherit_from` | a new pair inheriting the **lower** `sessions_correct` of those named |
| a live pair of this placement, absent from the set | **retired** — no longer drilled or shown, its misses kept |

So a **split** is the original reworded plus a new entry inheriting from it; a
**combine** is one new entry naming both originals in `inherit_from`, with both
falling out of the set. Combining takes the lower count deliberately: the weaker
of the two memories is the honest description of the merged one.

Call out splits and combines explicitly rather than leaving them to be noticed.

Nothing is ever deleted — miss rows point at pairs forever. And the store refuses
a set that would leave a placement with no live pair; if you hit that, report it.
