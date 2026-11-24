---
name: cg-spike-hello
description: "Host test for Compound GPID 2.0. Runs a probe script and reports what the host exposes."
disable-model-invocation: true
---

# Host probe

This skill exists only to test a coding agent host. It changes nothing.

1. Find the folder that holds this file. Say how you found it: the host told you the path, or you searched.
2. Run `scripts/probe.py` from that folder with Python. Try `python3`, then `python`, then `py -3`. Say which command worked and how many approval prompts the user saw.
3. Copy the script's output into your reply, unchanged.
4. Answer in one line each:
   - Do you have a todo or task-list tool? Name it.
   - Do you have a tool that starts a subagent with a fresh context? Name it.
   - Is the text `CG-SPIKE-POINTER` in your context right now? It is present only if the project's always-loaded instructions file was loaded.
   - Under what exact name did the user invoke this skill?

Done when all four answers and the script output are in the reply.
