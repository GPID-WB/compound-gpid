# Build REST APIs in R with `plumber`. Use `collapse` for fast computation inside endpoints.

## Startup: Load Data Once

Load reference datasets at startup (global scope) and use keyed lookup inside handlers. Never read data on every request.

```r
library(plumber)
library(collapse)
library(data.table)

# Load once at startup — shared across all requests
poverty_data <- load_all_poverty_data()
setkey(poverty_data, country_code, year)
```

## Programmatic Router

```r
pr() |>
  pr_get("/health", function() {
    list(status = "ok", timestamp = Sys.time())
  }) |>
  pr_get("/poverty/:country_code/:year", function(country_code, year, res) {
    if (!grepl("^[A-Z]{3}$", country_code)) {
      res$status <- 400L
      return(list(error = "Invalid country code"))
    }
    year <- as.integer(year)
    if (is.na(year) || year < 1990 || year > 2030) {
      res$status <- 400L
      return(list(error = "Invalid year"))
    }
    dt <- poverty_data[.(country_code, year)]   # O(log n) key lookup
    if (fnrow(dt) == 0) {
      res$status <- 404L
      return(list(error = "No data found"))
    }
    if (anyNA(dt$welfare) || anyNA(dt$weight) || any(dt$weight <= 0)) {
      res$status <- 500L
      return(list(error = "Data integrity error"))
    }
    list(country = country_code, year = year,
         mean_welfare = fmean(dt$welfare, w = dt$weight),
         headcount = fmean(dt$welfare < 2.15, w = dt$weight))
  }) |>
  pr_set_error(function(req, res, err) {
    message("API Error: ", conditionMessage(err))
    res$status <- 500L
    list(error = "Internal error")
  }) |>
  pr_set_api_spec(function(spec) {
    spec$info$title <- "GPID Poverty API"
    spec$info$version <- "1.0.0"
    spec
  }) |>
  pr_run(port = 8080)
```

## Input Validation

Always validate and convert types on path/query parameters:

```r
#* @get /stats/<country>/<year>
function(country, year, res) {
  if (!grepl("^[A-Z]{3}$", country)) {
    res$status <- 400L
    return(list(error = "Invalid country code"))
  }
  year <- as.integer(year)
  if (is.na(year) || year < 1990 || year > 2030) {
    res$status <- 400L
    return(list(error = "Invalid year"))
  }
  compute_stats(country, year)
}
```

## Authentication Filter

```r
auth_filter <- function(req, res) {
  if (req$PATH_INFO == "/health") return(plumber::forward())
  token <- req$HTTP_AUTHORIZATION
  if (is.null(token) || !validate_token(token)) {
    res$status <- 401L
    return(list(error = "Unauthorized"))
  }
  plumber::forward()
}
```

## CORS

```r
cors_filter <- function(req, res) {
  # For internal/authenticated APIs, replace "*" with a specific allow-list:
  # res$setHeader("Access-Control-Allow-Origin", "https://your-app.worldbank.org")
  res$setHeader("Access-Control-Allow-Origin", "*")
  res$setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
  if (req$REQUEST_METHOD == "OPTIONS") { res$status <- 200L; return(list()) }
  plumber::forward()
}
```

## Deployment

```r
# Posit Connect
rsconnect::deployAPI(api = "plumber.R", appName = "gpid-api")
```

Ensure `renv.lock` is committed — Connect uses it to rebuild the environment.
