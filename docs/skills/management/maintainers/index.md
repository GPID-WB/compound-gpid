# Maintainer Guide

Maintainer operations require one canonical development checkout on a
nondefault, nonprotected feature branch. Free-text role, origin, approver, or
review values cannot elevate a consumer context.

1. [Create](creation.md) a new permanent skill or [vendor](vendoring.md) an
   imported bundle.
2. Review [registry and capability](registry-capabilities.md) ownership.
3. [Update](updates.md) only from a new immutable full SHA.
4. [Deprecate and remove](deprecation-removal.md) with successor and grace proof.
5. Run the separate [release gates](release.md).

Read [security controls](../security.md) before any canonical mutation.
