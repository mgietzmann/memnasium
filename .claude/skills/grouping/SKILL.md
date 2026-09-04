---
name: grouping
description: Place newly entered memnasium notes into groups, or deliberately onto the roll. Use when the user says they have notes to group, asks what is waiting to be triaged, or wants to work the ungrouped queue. Requires `make run` to be up.
---

# Grouping

Built from `design/flows/Grouping.md`. Read that doc if anything here is unclear;
it is the specification and this is the working copy.

**You recommend and commit. The user decides every placement.** The groups are
the user's mental map, not your ontology.

## The pass

1. `list_ungrouped_notes` — notes with **no placement at all**. A note on the
   roll is not in this queue; it holds a placement and has been decided on.
2. `list_groups` — every group's name, description and note count. The
   **description is the matching key**.
3. For each note in the pass, offer the plausible fits with their note counts and
   one line of *why*:

   ```
   Note 512  Puget Sound: onset of piscivory 70 mm inshore, 130 mm offshore
     → Onset of piscivory (4 notes)  — regional thresholds for the same transition
     → What Chinook eat (22 notes)   — weaker; this is about a transition, not diet

   Note 519  Trawl surveys underestimate juvenile abundance nearshore
     → nothing matches. Closest is Sampling bias (2 notes) and it is not close.
   ```

   Where a recommendation turns on something the description does not settle,
   `get_group` for that group's notes and say what you found.
4. The user answers the whole pass in one message: group X · X and Y · the roll ·
   a new group named Z.
5. Commit with `place_notes`. Decisions commit as they are given — arguing about
   note 519 does not un-commit note 512.

## Rules you do not get to bend

- **"Nothing matches" is a real answer.** A recommender that always recommends is
  noise, and the roll is a legitimate destination, not a failure.
- **Never coin a group.** New groups exist because the user asked for one. You may
  draft the description for approval, then `create_group` — that is capture, not
  decision.
- **Descriptions first, notes on demand.** Pull a group's notes only when a
  candidate is borderline.
- **Size is shown, not judged.** List the note count. Whether a group is getting
  fat is the user's call.
- **Flag, do not act.** Say out loud when a description has drifted, or when roll
  notes look like they belong with a group just created — the second is a handoff
  to the `regrouping` skill, not something you do here.

## What a placement means

Every placement lands with **no pairs**, which is exactly what puts it in the
`wordsmithing` queue. Placing a note is not the end of the work.

A note on the roll may not also hold a group placement, so promoting a roll note
is `move_placement`, never a second `place_notes`. The store refuses it either
way; do not work around a refusal, report it.
