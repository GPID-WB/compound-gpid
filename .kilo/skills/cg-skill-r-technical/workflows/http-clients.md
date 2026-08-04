# HTTP Clients with httr2

Build HTTP clients in R with `httr2`. Prefer `httr2` over `httr` (the older package) for all new code — `httr2` has a pipeline-based API, built-in retry logic, and better error handling.

## Basic Request Pattern

```r
library(httr2)

# Simple GET
resp <- request("https://api.example.com/data") |>
  req_headers(Accept = "application/json") |>
  req_perform()

# Parse JSON response
data <- resp |> resp_body_json()
```

## Authentication

```r
# Bearer token (most common for World Bank APIs)
resp <- request(base_url) |>
  req_auth_bearer_token(Sys.getenv("API_TOKEN")) |>
  req_perform()

# Basic auth
resp <- request(base_url) |>
  req_auth_basic(username, password) |>
  req_perform()

# API key as query parameter
resp <- request(base_url) |>
  req_url_query(apikey = Sys.getenv("API_KEY")) |>
  req_perform()
```

Never hardcode credentials. Always read from environment variables (`Sys.getenv()`).

## Query Parameters and URL Building

```r
# Add query parameters
resp <- request("https://api.worldbank.org/v2/country") |>
  req_url_query(
    format   = "json",
    per_page = 100,
    page     = 1
  ) |>
  req_perform()

# Build URL path segments
resp <- request("https://api.example.com") |>
  req_url_path_append("poverty", country_code, year) |>
  req_perform()
```

## Error Handling

```r
# Check for HTTP errors (throws on 4xx/5xx)
resp <- request(url) |>
  req_perform() |>
  resp_check_status()

# Handle errors gracefully
resp <- tryCatch(
  request(url) |> req_perform() |> resp_check_status(),
  httr2_http_404 = function(e) {
    cli::cli_warn("Resource not found: {url}")
    NULL
  },
  httr2_http_429 = function(e) {
    cli::cli_abort("Rate limit exceeded. Retry after {resp_header(e$resp, 'Retry-After')}s.")
  }
)
```

## Retry Logic

```r
# Automatic retry with exponential backoff
resp <- request(url) |>
  req_retry(
    max_tries    = 3,
    is_transient = \(resp) resp_status(resp) %in% c(429, 500, 503),
    backoff      = \(i) 2^i  # 2s, 4s, 8s
  ) |>
  req_perform()
```

## Pagination

```r
# req_perform_iteratively: follow next-page links automatically
resps <- request("https://api.example.com/data") |>
  req_url_query(per_page = 100) |>
  req_perform_iteratively(
    next_req = \(resp, req) {
      body <- resp_body_json(resp)
      if (!is.null(body$next_page_url))
        req_url(req, body$next_page_url)
      else
        NULL  # Stop pagination
    }
  )

# Combine results
all_data <- resps |>
  lapply(\(r) resp_body_json(r)$data) |>
  rbindlist()
```

## Parallel Requests

```r
# Fetch multiple URLs concurrently
urls <- paste0("https://api.example.com/country/", country_codes)

resps <- urls |>
  lapply(request) |>
  req_perform_parallel(on_error = "continue")

# Extract results, skip failures
results <- resps |>
  lapply(\(r) if (inherits(r, "httr2_response")) resp_body_json(r) else NULL) |>
  Filter(Negate(is.null), x = _) |>
  rbindlist()
```

## Common World Bank API Pattern

```r
#' Fetch poverty data from the PIP API
#'
#' @param country ISO3 country code
#' @param year Survey year
#' @param poverty_line Poverty line in 2017 PPP USD/day
#' @return data.table with poverty estimates
fetch_pip <- function(country, year, poverty_line = 2.15) {
  resp <- request("https://api.worldbank.org/pip/v1/pip") |>
    req_url_query(
      country       = country,
      year          = year,
      povline       = poverty_line,
      fill_gaps     = FALSE,
      welfare_type  = "consumption",
      reporting_level = "national",
      format        = "json"
    ) |>
    req_retry(max_tries = 3) |>
    req_perform() |>
    resp_check_status()

  as.data.table(resp_body_json(resp, simplifyVector = TRUE))
}
```
