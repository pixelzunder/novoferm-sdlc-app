# Bonus B2 - Spec first

## Intro

"Add a quantity discount" is one sentence, and it hides a dozen decisions: from how many doors,
on which doors, how to round, what happens to the existing answer of the API. An agent that
starts coding makes these decisions silently, and you find them in the diff - or you do not.

A better prompt is one way out. This exercise takes the other one: the agent asks, you answer,
and the answers are written down before any code exists.

## Task

Start from `solution/b1-context-diet`.

1. **Try it the short way.** On a throwaway branch, prompt `Add a quantity discount.` and let
   the agent build. Read the diff and list every decision it made without asking you.
   Throw the branch away.
2. **Write the skill.** Create a skill `spec` that makes the agent read only what the feature
   touches, interview you with options and a recommendation, write
   `docs/specs/<feature>.md`, and then stop for your approval.
3. **Get interviewed.** Run `/spec Add a quantity discount.` and answer the questions. Check
   the spec: are the examples calculated, and can every acceptance criterion become a test?
4. **Build from the spec.** Approve it and let the agent implement: tests first, one per
   acceptance criterion, then the code.

## Outcome

- `.claude/skills/spec/SKILL.md` - the method, reusable for the next feature
- `docs/specs/quantity-discount.md` - decisions, examples and acceptance criteria
- the quantity discount on the command line, in the JSON API and on the page, with
  `tests/test_quantity.py` written before the implementation

Your spec will differ from the one in this branch: the decisions are yours.

## What you learn

- A vague prompt is not a short prompt, it is a prompt with hidden decisions.
- Letting the agent interview you is cheaper than writing the perfect prompt, and it finds
  questions you would not have thought of.
- A spec with calculated examples is the test list. Compare your list from step 1 with the
  decision table: that difference is what the interview bought you.
