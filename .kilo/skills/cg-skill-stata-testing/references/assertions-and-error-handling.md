# Assertions and Error Handling in Stata

## Core Assertion Syntax

```stata
* Basic assertion — halts with error if condition is false
assert condition

* Assertion with qualifier
assert condition if in_sample

* Assert on stored result
count if missing(welfare)
assert r(N) == 0
```

## Capturing Errors with `capture`

`capture` suppresses the error display and stores the return code in `_rc`. Use it to implement soft assertions — ones that warn without halting.

```stata
capture assert condition
if _rc {
    display as error "FAIL: condition not met"
    // optionally: error _rc  // re-throw to halt
}
```

Key distinction:
- `capture assert ...` — suppresses error, stores code in `_rc`
- `capture noisily assert ...` — shows error output but continues; useful for diagnosis

## Return Codes (`_rc`)

Stata stores the exit code of the last `capture`d command in `_rc`:
- `_rc == 0` — success
- `_rc == 9` — assertion failed (`assert` returned non-zero)
- `_rc == 1` — user break
- Other values indicate specific command errors

```stata
capture assert age >= 0
if _rc == 9 {
    count if age < 0
    display as error "FAIL: `r(N)' observations have negative age"
}
else if _rc != 0 {
    display as error "UNEXPECTED ERROR: _rc = `_rc'"
    error _rc
}
```

## Exit Codes for Custom Error Signaling

Use `exit` or `error` to halt with a meaningful code when a critical validation fails:

```stata
* error N: halts and displays Stata error N
count if missing(welfare) & !missing(weight)
if r(N) > 0 {
    display as error "CRITICAL: `r(N)' weighted observations have missing welfare"
    error 459    // 459 = "variable has missing values"
}
```

Prefer `error N` (uses Stata's error catalog) over `exit N` (silent exit). For custom messages, pair `display as error` + `error 198` (generic user error).

## Structured Assertion Blocks

Group related assertions with section headers to aid diagnosis:

```stata
* ---- 1. Validate input data ----
assert !missing(welfare)
assert !missing(weight)
assert weight > 0

* ---- 2. Validate PPP conversion ----
assert !missing(ppp_2017)
assert ppp_2017 > 0
assert inrange(ppp_2017, 0.01, 10000)

* ---- 3. Validate computed results ----
assert !missing(welfare_ppp)
assert welfare_ppp >= 0
```

## Assertion with Context Message

Always pair an assertion with a `count` or `display` that shows how many observations failed, not just that they did:

```stata
* Verify no negative welfare values after PPP conversion
count if welfare_ppp < 0
local neg_count = r(N)
if `neg_count' > 0 {
    display as error "FAIL: `neg_count' observations have negative welfare_ppp"
    error 459
}
assert `neg_count' == 0
```

## Soft Assertion Pattern (Warn but Continue)

For non-fatal checks where you want a warning without halting:

```stata
capture assert inrange(ppp_2017, 0.5, 200)
if _rc {
    count if !inrange(ppp_2017, 0.5, 200)
    display as result "WARNING: `r(N)' PPP values outside expected range (0.5–200)"
    // continue — this is a warning, not an error
}
```

## `capture` vs `capture noisily`

| Pattern | Error output | Continues? | Use when |
|---------|-------------|------------|---------|
| `capture assert ...` | Suppressed | Yes | Soft assertion, check `_rc` manually |
| `capture noisily assert ...` | Displayed | Yes | Diagnosis — see what failed without halting |
| `assert ...` (no capture) | Displayed | No (halts) | Hard assertion — test must pass |

## Display Style Conventions

```stata
display as error "FAIL: description of what went wrong"   // red — assertion failures
display as result "PASS: description of what passed"       // default — successes
display as text "INFO: supplementary information"          // plain text — context
```

Use `as error` for failures even in soft assertions — it ensures failures are visible regardless of log settings.
