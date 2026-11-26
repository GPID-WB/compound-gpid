---
id: P12
name: Governed data
applies-when: "the work reads, produces or describes any dataset, or any information about a person"
stages: "plan, review"
verifier: governance
status: accepted
derived-from: "general data governance practice: information classification, data privacy principles, disclosure of AI use; docs/philosophy.md (organizational risks); compound-gpid.md (constraints)"
---

# P12 Governed data

Before an agent touches a dataset, its classification, source and permitted use are known. Restricted data and personal data stay inside the tools approved for them. The part AI played in the work is recorded and disclosed.

**Why.** When an agent reads a file, the contents go to the company that runs the model. That is a transfer of data, and for much of what analysts hold it is not allowed. Classification, privacy and disclosure rules bind the human whether or not the tool reminds them, and the human is the one accountable.

**The human answers for the data.** The plugin records what the human declares and cannot check it: a file the human declares Public is treated as Public. The human may also decide that a coding agent reads a file it is not cleared for. The agent warns them first, code records the decision, and the work goes on. A stop is there to get the human's decision. It does not overrule one.

This principle states general working rules. It is not any organization's policy and does not replace one. Where the two differ, the policy wins, and the human asks the responsible office.

Terms used here are defined in the plugin glossary (`../GLOSSARY.md`): classification, restricted data, personal data, data register, approved tool, lineage, AI-use statement.

## In production

### Setup

- Record the organization's classification scheme in the project configuration: the names of its levels, from public to most restricted.
- Ask the human which AI tools are approved for which level, and record the answer. The agent does not judge approval; it records what the human declares.
- Record the classification the human gives each data file found. A file with no recorded classification is restricted data.

### Plan

- Write the data register: every dataset the work will use, with its classification, source, version, owner and permitted use.
- Treat a dataset with no known classification as restricted data. Stop and ask the human, who asks the data owner if they do not know.
- Compare the highest classification in the register with what the current tool is approved for. If the tool is not approved, say so before reading anything, and plan the work so the agent sees no restricted data: it writes and reviews code, and works from the schema, from public data or from a synthetic sample.
- The human may decide that the agent reads the data all the same. Warn them before they decide: reading a file sends its contents to the company that runs the model, their organization's rules bind them, and the decision is recorded under their name. Record it with `cg.py approve --reads` before the file is opened: their reply word for word, their name, the time, the file and its classification. The decision holds for that coding agent, for the file or folder the human named, and for that classification. Another coding agent, another place or a new classification asks for a new decision.
- Give every output a classification. An output made from restricted data is restricted until the data owner says otherwise.
- If the work builds a new system that processes personal data, tell the human to ask the privacy office whether an assessment is needed before it is deployed.

### Work

- Read a dataset only after the register and the tool check are done.
- In a tool that is not approved for the data, never print, paste or summarize rows or values, unless the human's recorded decision lets this coding agent read the file. Run code and report only what the plan allows: an exit code, a row count, a check that passed or failed.
- Keep restricted data, personal data and credentials out of code, prompts, logs, commits, artifacts and evidence. Evidence holds digests and counts.
- Use the least personal data the purpose needs, and only for that purpose. Pseudonymize where the analysis allows. Keep it no longer than the purpose needs.
- Record lineage: which version of which input produced each output.
- Use data and code only as their licence and access terms allow. Do not reproduce a dataset, a text or a brand asset the project has no right to.

### Sign-off

- Attach the AI-use statement to the defend-it brief: the tool and model, what it contributed, the sources it worked from, and who reviewed the output. The human can place it in the official work where disclosure is required.

## Who to ask

The agent does not settle a question of policy, such as whether a tool is approved, how a file is classified, or whether personal data may be used. It names the open question and says that the answer comes from the human's organization: from whoever is responsible there for the use of AI, for information security or for personal data. The human asks, and the agent records the answer.

## Evidence it leaves

- The data register, in the plan.
- The human's declaration of which tools are approved for which classification, in the project configuration.
- Each decision of the human to let a coding agent read data it is not cleared for, one file per decision under `.cg-docs/approvals/`.
- Lineage for each output.
- The AI-use statement.
- A repository history with no data files, no personal data and no credentials.

## Verifier: `governance`

**At plan stage, inspect** the data register and the tool declaration. **At review stage, inspect** the diff, the artifacts, the evidence and the outputs.

Flag when:

- a dataset is used and is not in the register, or has no classification, source or version;
- the register holds data above what the current tool is declared approved for, and the plan lets the agent read it with no recorded decision of the human;
- rows or values from restricted data appear in a commit, an artifact, an evidence entry or a prompt file;
- personal data is hardcoded, logged or committed, or more of it is used than the stated purpose needs;
- a credential or token appears anywhere;
- an output from restricted data carries no classification, or a lower one with no decision by the data owner;
- an output cannot be traced to the versions of its inputs;
- the AI-use statement is missing or leaves out the tool, the contribution or the reviewer.

**Prove a flag** by pointing at the `file:line`, or at the register row that is missing or incomplete.

A flag for exposed restricted data, exposed personal data or an exposed credential is priority P0.

**Leave alone:** whether a tool should be approved, whether a classification is right, and whether the human was right to let the agent read a file. Those belong to the human and the responsible offices. Report doubt under `not-checked`.

## Deterministic checks

- Every dataset path the code reads appears in the data register with a classification.
- `cg.py tier` raises the tier when a data file the work reads is not cleared for the current tool and no decision of the human to read it is recorded. A file is cleared when its recorded classification is Public, or is the one the tool is declared approved for or a less restricted one in the organization's scheme. A folder that the work reads is held to every rule recorded below it. Once a decision is recorded, `tier` names it on every run.
- A search of changed files for data files, credential patterns and row-level content.
- Evidence entries contain digests and counts only.
- The AI-use statement is present before sign-off is offered.
