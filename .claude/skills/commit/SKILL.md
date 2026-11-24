---
name: commit
description: Write the commit message for this repository and create the commit. Use whenever you are asked to commit, to write or fix a commit message, or to prepare changes for a pull request.
---

# Commit

Commit messages in this repository follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
with two additions: an emoji and a ticket number.

## Format

```
<type>(<scope>): <emoji> <description>

<body: why the change was made, wrapped at 72 characters>

Refs: DOOR-<number>
```

Example:

```
feat(pricing): ✨ add insulation priced per square metre

Customers can choose single, double or thermo insulation. The price is
data in rules.json and rounded half up like the panel price.

Refs: DOOR-12
```

## Type and emoji

| Type | Emoji | Use for |
|---|---|---|
| `feat` | ✨ | new behaviour a user can see |
| `fix` | 🐛 | a bug fix |
| `test` | 🧪 | tests only |
| `docs` | 📝 | README, AGENTS.md, comments |
| `refactor` | ♻️ | same behaviour, better structure |
| `chore` | 🔧 | tooling, configuration, dependencies |
| `ci` | 🤖 | pipeline and hooks |

## Rules

- **Scope** is the module or area: `rules`, `pricing`, `cli`, `web`, `messages`, `data`,
  `tests`, `harness`. Leave it out when the change touches everything.
- **Description**: imperative, lower case, no full stop, at most 72 characters for the whole
  first line.
- **Body**: says why, not what. The diff shows what. Leave it out for trivial changes.
- **Breaking change**: `!` after the scope and a `BREAKING CHANGE:` footer. Renaming a violation
  code or a command line argument is breaking.
- **One topic per commit.** If the description needs "and", split the commit.

## Ticket number

1. Take it from the branch name when it has one (`feature/DOOR-12-insulation` -> `DOOR-12`).
2. Otherwise take it from the conversation when the user named a ticket.
3. Otherwise **ask the user**. Do not invent a number and do not leave the footer out.
   When the user says there is no ticket, write `Refs: none`.

## Steps

1. Run `git status` and `git diff --staged`. When nothing is staged, show what would be
   committed and ask before staging. Never use `git add -A` blindly.
2. Check the branch: never commit on `main`.
3. Run the tests (`python -m pytest`). Do not commit when they fail, unless the commit is a
   deliberately red test commit (`test: 🧪 ...`) and the body says so.
4. Write the message in the format above and show it to the user.
5. Commit. Never use `--no-verify`.
