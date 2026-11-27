---
name: governance
principle: P12
derived-from: "addyosmani/agent-skills@e997ac5:skills/security-and-hardening/SKILL.md; v1:.agents/skills/cg-version-control.md"
---

# Lens: governance

This lens is for the verifier of P12. It says what code holds, what is left to your judgement, how each flag is proved and the change each fix proposes. It adds to the section "Verifier" of your principle file and takes nothing from it.

## What code holds

- `cg.py tier` decides from the data rules of `.cg-docs/config.json` whether this coding agent may read each data file, and `cg.py approve --reads` records the human's decision to read one that is not cleared; status lists those decisions under `data-decisions`. At the plan stage `cg.py validate` held the data register to the recorded classifications.
- A record of evidence holds a digest and counts, and never what a check printed.
- No code searches the change for a credential, a data file or a row of one: you do, in the files that differ from the commit your kickoff names, and in the commits since.
- Your kickoff clears no data file (rule 6 of `verifier.md`): you read its name and the code that reads it, never its rows.

## At the plan stage

Read the data register, the shape of the data below it, and the plan's Never list. Flag:

- a dataset the plan reads or writes that the register does not list, or lists with no source, version or owner;
- an output made from restricted data with no classification, or a lower one with no decision of the data owner;
- a slice that opens a dataset the `data` line of `tier` calls not cleared, with no decision of the human on record;
- personal data used beyond what the goal needs, or kept with no end.

Point at the line of the plan or the row of the register.

## The flags

| Flag | You judge | Fix: the change to propose | Priority |
|---|---|---|---|
| A credential in the change | a token, a password, a key or a connection string in code, a configuration, a notebook, a test or a commit; `.Renviron` or `.env` that git does not ignore | the value read from the environment, such as `Sys.getenv("API_TOKEN")`, the file ignored by git, and the human told to rotate it | P0 |
| Rows of restricted data where they do not belong | a data file, a sample or a print of it, or an output made from it, in a commit, an artifact, the evidence, a log or a test fixture | the file out of the commit and ignored by git; a fixture that code builds from no real row | P0 |
| Personal data in code, or more than the purpose needs | a name, an identifier or an address typed into code, a log or a figure; a column of personal data the goal does not use kept or joined | the identifier dropped, or pseudonymized where the analysis allows | P0 |
| A dataset read that the register does not list | a path the code reads that no row of the register names | the row in the register, through an amendment the human approves | P1 |
| An output with no classification | an output made from restricted data that the register does not list, or lists at a lower level | the output in the register at the level of its inputs | P1 |
| An output with no lineage | nothing records which version of which input made the output | the version and the date of each input, in the register or beside the output | P2 |
| A large or binary data file tracked by git | a file of data, a database or an archive that the change adds to git | the file ignored by git and kept where its rule says | P2 |

## Prove and propose

- Point at the line, `path:line`, that holds the credential or reads the data, or at the row of the register. A file that git tracks and should not: point at the line of `.gitignore` where its rule belongs.
- Never copy the credential, a value or a name into a finding (rule 6): say what kind of thing it is. A credential that reached a shared remote is exposed for good: say in the finding that the human has it rotated.
- Write each finding as rule 4 of `verifier.md` says, with the priority of its row and `fix:` with the change of its row. An exposed credential, exposed personal data and exposed restricted data are P0.

## Leave alone

Whether a tool should be approved, whether a classification is right, and whether the human was right to let an agent read a file: those are the human's and their organization's (P12). The AI-use statement, which sign-off asks for. Say in your note what you left and why.
