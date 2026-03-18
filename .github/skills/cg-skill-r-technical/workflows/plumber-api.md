# Plumber APIs

## Minimal API Example

```r
# R/api.R
library(plumber)

#* @apiTitle GPID Data API
#* @apiDescription API for accessing GPID poverty data

#* Health check
#* @get /health
function() {
  list(status = "ok", time = Sys.time())
}

#* Get poverty headcount by country
#* @param country ISO3 country code
#* @param year Reference year
#* @get /poverty
function(country, year) {
  year <- as.integer(year)
  get_poverty_data(country = country, year = year)
}
```

## Starting the API

```r
# Run interactively
pr("R/api.R") |> pr_run(port = 8000)

# Or via entrypoint.R
# plumber::plumb("R/api.R")$run(port = 8000)
```

## Request and Response Serializers

```r
#* Return JSON (default)
#* @serializer json
#* @get /data

#* Return CSV
#* @serializer csv
#* @get /data/csv

#* Return unboxed JSON (single values as scalars)
#* @serializer unboxedJSON
#* @get /scalar
```

## Input Validation

```r
#* @param country ISO3 country code (3 uppercase letters)
#* @get /country
function(country, res) {
  if (!grepl("^[A-Z]{3}$", country)) {
    res$status <- 400
    return(list(error = "country must be a 3-letter ISO3 code"))
  }
  get_data(country)
}
```

## Filters (Middleware)

```r
#* Log all requests
#* @filter logger
function(req, res) {
  cat(format(Sys.time()), req$REQUEST_METHOD, req$PATH_INFO, "\n")
  plumber::forward()
}

#* Require API key
#* @filter auth
function(req, res) {
  key <- req$HTTP_X_API_KEY
  if (is.null(key) || key != Sys.getenv("API_KEY")) {
    res$status <- 401
    return(list(error = "Unauthorized"))
  }
  plumber::forward()
}
```

## OpenAPI / Swagger

```r
# Auto-generated at /openapi.json
# Interactive UI at /__docs__/
pr("R/api.R") |>
  pr_set_api_spec(function(spec) {
    spec$info$title <- "GPID API"
    spec$info$version <- "1.0.0"
    spec
  }) |>
  pr_run(port = 8000)
```

## Error Handling

```r
#* @get /safe-endpoint
function(req, res) {
  tryCatch(
    risky_operation(),
    error = function(e) {
      res$status <- 500
      list(error = conditionMessage(e))
    }
  )
}
```

## Project Structure for APIs

```
my-api/
├── R/
│   ├── api.R           # Plumber endpoint definitions
│   ├── handlers.R      # Business logic (called by endpoints)
│   └── utils.R         # Shared utilities
├── tests/
│   └── testthat/
│       └── test-handlers.R  # Test handlers directly (not via HTTP)
├── entrypoint.R        # Entry point for deployment
└── DESCRIPTION
```

Test handler functions directly rather than making HTTP calls in tests.
