# Info Workflow

1. Resolve the same canonical catalog used by `find`.
2. Match one immutable identifier exactly.
3. Return owner, source, provenance identity, selectors, supported suites and
   platforms, activation cost, and the inactive or prospective reason.
4. Return `skill.unknown` for an absent identifier and do not search global or
   external skill locations.
