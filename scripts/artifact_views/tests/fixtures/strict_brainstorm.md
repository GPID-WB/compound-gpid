---
artifact-schema-version: 1
date: 2026-07-31
title: "Strict Brainstorm"
status: decided
scope: "Standard"
chosen-approach: "Deterministic parser"
tags: [brainstorm, parser]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Strict Brainstorm

## Context

Humans and agents need different views of one canonical artifact.

## Requirements

- Preserve Markdown authority.
- Validate before rendering.

## Approaches Considered

### Approach 1: Deterministic parser

Parse a closed grammar without model calls.

### Approach 2: Generic conversion

Use a generic Markdown renderer with weaker semantic structure.

## Decision

Use the deterministic parser because it preserves structural meaning.

## Next Steps

1. Define the executable contract.
2. Implement validation.
