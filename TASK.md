# Bonus B1 - Context diet

## Intro

Everything a coding agent reads costs tokens: your prompt, the files it opens, and the briefing
in `AGENTS.md` - that one in every session and with every request. Since D3 the briefing has
grown with every exercise. Part of it is needed for every task, part of it only for some.

This exercise is about spending fewer tokens for the same result: load less by default, load
the rest on demand, and work in a way that keeps the context small.

## Task

Start from `solution/d8-fitness-functions`.

1. **Measure.** Open a new session and run `/context`. How much of the window is filled
   before you typed anything, and by what?
2. **Compare two prompts.** Ask for the same small change twice, each in a new session, and
   note `/context` and `/cost` afterwards. Throw both results away.
   - vague: `Look at the project and add a surface "brushed" for 119 EUR per m2.`
   - precise: `Add a surface "brushed" at 11900 cents per m2 in @data/rules.json. Test first
     in @tests/test_pricing.py.`
3. **Put the briefing on a diet.** Go through `AGENTS.md` line by line: does every task need
   this? Move what only some tasks need into skills, and delete what repeats something the
   agent learns anyway.
4. **Use the small model.** Turn the translation prompt of D7 into a subagent that runs on the
   small model in its own context.
5. **Keep the weight off.** Add a fitness function that fails when the briefing grows beyond
   a budget.

## Outcome

- `AGENTS.md` with about 2,500 instead of 4,300 characters, nothing lost
- the skills `add-rule-entry` and `check-page`, the subagent `translator`
- two fitness functions in `tests/test_architecture.py` for the context budget
- the section "Context budget" in the README

Your numbers from steps 1 and 2 are the real result: write them down before and after.

## What you learn

- What is always loaded is paid for every time. A skill costs one line until it is used.
- A precise prompt with named files saves more than any setting: the agent reads one file
  instead of searching twenty.
- Habits count: one task per session (`/clear`), let a subagent search, small model for
  mechanical work.
- A budget that is not tested does not last.
