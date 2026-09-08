# Manage Registry and Capabilities

Every canonical asset has exactly one module owner. A capability identifies its
owning module, supported suites and platforms, source provenance, activation
cost, task triggers, and selectors. Dependencies can add required capabilities;
configuration cannot subtract them.

Project records use reserved owner `project-local`, capability
`project-skill-<id>`, explicit-only activation, and one-to-one selected-bundle
mapping. Project records cannot shadow canonical identifiers, owners, or
capabilities.

Run module ownership, dependency, and cross-suite checks before [release](release.md).
