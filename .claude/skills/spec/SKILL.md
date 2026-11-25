---
name: spec
description: Turn a feature idea into a written spec by interviewing the user, before any code. Use for every feature that changes rules, prices or the answer of the API, and for one-line requests.
---

# Spec first

A one-line request hides decisions. If you start coding, you make them silently, and the user
finds them in the diff. Ask first, write the answers down, get a yes, then build.

## 1. Read, but only what the feature touches

The section of `README.md` on the modules involved, `data/rules.json`, and the tests of those
modules. Do not ask the user what the code can tell you.

## 2. Interview

Ask until no open question would change a test. Rules for the interview:

- One topic per question, at most three questions at a time.
- Offer options and say which one you recommend and why. "A or B? I would take A, because
  ..." is answered in seconds; "how should it work?" is not.
- Use numbers from this project in every example, for example the base door at 944.00 EUR.

Topics to cover. Skip one only when it clearly does not apply:

| Topic | What to find out |
|---|---|
| Behaviour | What exactly happens, in the user's words and in one example |
| Input | New fields, their default, their limits, what is a violation |
| Money | What is rounded, when, and in whose favour |
| Existing answers | Does anything change for a request that works today? |
| Front ends | Command line, JSON API and page: all three, and what the page shows |
| Edge cases | The smallest and largest value, the value just below a threshold |
| Out of scope | What somebody could expect that will not be built now |

## 3. Write the spec

`docs/specs/<feature>.md` with these sections, in this order:

1. **Goal**: one or two sentences, and who asked for it.
2. **Decisions**: a table of question, decision and reason. Every answer of the interview.
3. **Behaviour**: data in `rules.json`, calculation, violations, the answer of the API.
4. **Examples**: a table with inputs and expected numbers. You calculated every one of them.
5. **Acceptance criteria**: a numbered list. Each one can be checked by a test.
6. **Out of scope**
7. **Open questions**: empty before the implementation starts.

The first line under the title is the status: `Status: draft`, `approved` or `implemented`.

## 4. Stop

Show the spec and ask for approval. Do not write tests or code in the same step. Change the
spec until the user says yes, then set the status to `approved`.

## 5. Build from the spec

- Tests first, one per acceptance criterion, with the numbers of the examples. See them fail.
- Implement until they are green. When the code teaches you that the spec is wrong or
  incomplete, stop, ask, and change the spec first.
- Set the status to `implemented` in the same change, and keep the README true.
