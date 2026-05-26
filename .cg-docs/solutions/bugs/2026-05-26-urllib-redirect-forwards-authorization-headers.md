---
date: 2026-05-26
title: "urllib.request follows redirects and forwards Authorization headers"
category: "bugs"
language: "Python"
tags: [security, urllib, http, redirect, authorization, bearer-token, credential-leak, github-api, ssrf]
root-cause: "urllib.request.urlopen follows HTTP 3xx redirects transparently and forwards all original request headers — including Authorization — to the redirect target, enabling a malicious server to capture Bearer tokens via a redirect to an attacker-controlled URL."
severity: "P0"
---

# urllib.request follows redirects and forwards Authorization headers

## Problem

Python's `urllib.request.urlopen` follows HTTP 3xx redirects automatically
by default. When the redirected request is sent to the new URL, it forwards
**all headers from the original request**, including `Authorization`.

In a GitHub Contents API client that uses `Bearer <token>` authentication,
this means:

1. Client sends `PUT /repos/{owner}/{repo}/contents/{path}` with
   `Authorization: Bearer ghp_xxxx`.
2. A misconfigured or malicious GitHub endpoint returns `301 Moved Permanently`
   to `https://attacker.example.com/steal`.
3. `urllib.request` transparently follows the redirect and sends the same
   `PUT` request — including `Authorization: Bearer ghp_xxxx` — to
   `attacker.example.com`.

The token can now be exfiltrated without the caller's knowledge, since no
exception is raised and the response from the attacker's server looks like a
normal HTTP response.

The same risk applies to any API that uses `Authorization`, `Cookie`,
`X-Api-Key`, or other credential headers.

## Root Cause

`urllib.request.HTTPRedirectHandler` (the default redirect handler installed
in the default opener) copies all headers when building the redirect request
via `redirect_request`. Although the HTTP spec (RFC 9110) recommends that
clients remove the `Authorization` header when the redirect crosses hosts or
schemes, Python's standard library does not implement this rule.

```python
# ❌ Vulnerable — default opener follows redirects, forwards headers
import urllib.request

req = urllib.request.Request(
    url,
    data=...,
    headers={"Authorization": f"Bearer {token}", ...},
    method="PUT",
)
with urllib.request.urlopen(req, timeout=30) as resp:  # may follow redirect!
    ...
```

## Solution

Install a custom `HTTPRedirectHandler` that **raises** on any redirect rather
than following it. This completely eliminates the risk — redirects become
visible errors instead of silent credential forwarding:

```python
import urllib.request
import urllib.error


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Block all HTTP redirects to prevent Authorization header forwarding."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(
            req.full_url,
            code,
            f"Redirect to {newurl!r} blocked; possible credential forwarding risk",
            headers,
            None,
        )


_opener = urllib.request.build_opener(_NoRedirectHandler())


def _api_request(req: urllib.request.Request, ...) -> dict:
    with _opener.open(req, timeout=30) as resp:   # ✅ safe — redirects raise
        ...
```

Build the opener once at module level. Use `_opener.open(req, ...)` instead
of `urllib.request.urlopen(req, ...)` everywhere in the module.

### Why not `urlopen` with a custom opener?

`urllib.request.urlopen` uses the *global* opener. Calling
`urllib.request.install_opener(_opener)` would replace it globally,
affecting other code in the same process. Using a module-level `_opener`
object limits the effect to this module.

## Prevention

- Any Python module that sets an `Authorization` header with
  `urllib.request` should install `_NoRedirectHandler` at module level.
- Consider using `httpx` instead of `urllib.request` for new code — it
  does not follow cross-origin redirects with credential headers by default
  and offers a cleaner API.
- Code review checklist item: "Does this `urlopen` call include credential
  headers? If so, is a `_NoRedirectHandler` or equivalent installed?"

## Related

- SEC-P0.1 in `.cg-docs/reviews/2026-05-21-knowledge-brain-engine-review.md`
  — the security finding this fix resolves.
- `.cg-docs/solutions/testing-patterns/2026-03-17-httpx-async-client-asgi-transport.md`
  — `httpx` as an alternative HTTP client with safer defaults.
- OWASP Server-Side Request Forgery (SSRF) — redirect-based SSRF is a
  related attack vector where open redirects on trusted servers forward
  requests to internal hosts.
