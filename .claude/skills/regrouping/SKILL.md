---
name: regrouping
description: Reshape memnasium's existing groups — split one that has grown too big, harvest a group out of the roll, or give a note context. Use when the user says a group is unworkable, asks what is sitting in the roll, wants notes pulled on a theme, or asks what they keep blowing. Requires `make run` to be up.
---

# Regrouping

Built from `design/flows/Regrouping.md`. Read that doc if anything here is
unclear.

**The user decides a group is wrong.** Trouble in a morning's drilling is the
signal, and only the user feels it. Never volunteer that a group needs splitting.

## Four ways in

| Way in | What the user says | What you do first |
|---|---|---|
| A group is too big | "*Productivity in upwelling systems* is unworkable" | `get_group` — its notes and its pair count, read together |
| A hunch | "Pull me everything that mentions spawning timing" | `search_notes` and show what came back |
| The roll is deep | "What patterns are still sitting in the roll?" | `search_notes(roll=true)` and describe the clusters you see |
| Something keeps failing | "What have I been blowing?" | `list_misses` — which pairs, in which groups, how often |

The third is the only one where you propose a shape, and even there you describe
what you see rather than creating anything.

## Pulling notes

`search_notes` filters compose: by group, by the roll, by source, by text in the
statement — everything from one source mentioning `piscivor` is one call. Group
descriptions are read with `list_groups`, so "pull the groups whose descriptions
look relevant" is you choosing the ids and then pulling by group.

The drill record is evidence. "These are giving me trouble" is a feeling first and
a query second: `list_misses` says which pairs have actually been blown, and how
often. You read them; the user still decides.

## Settling a group

The user names it. You draft a description for approval, then `create_group`,
then search for members and propose them **with their statements** so the user
can strike the ones that do not belong. Nothing moves until the list is confirmed.

## Moving

- `move_placement` rewrites the placement's group and sets `pairs_stale = 1`. The
  pairs travel with it, keeping `sessions_correct` — the memory was real even if
  the wording now needs redoing.
- Moving a note **off the roll** updates its existing placement. Moving a note
  **between groups** updates that placement.
- Adding a note to a **further** group is `place_notes` — a new placement with no
  pairs, a fresh set of questions for the new context.
- A group emptied by a move is deleted for you.

Every moved or new placement is now in the `wordsmithing` queue. Say so.
