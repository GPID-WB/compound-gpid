# Plumber APIs

Build REST APIs in R with `plumber`. Use `collapse` for fast computation inside endpoints.

## Programmatic Router

```r
library(plumber)
library(collapse)
library(data.table)

pr() |>
  pr_get("/health", function() {
    list(status = "ok", timestamp = Sys.time())
  }) |>
  pr_get("/poverty/:country_code/:year", function(country_code, year, res) {
    year <- as.integer(year)
    if (!grepl("^[A-Z]{3}$", country_code)) {
      res$status <- 400L
      return(list(error = "Invalid country code"))
    }
    dt <- load_poverty_data(country_code, year)
    if (fnrow(dt) == 0) {
      res$status <- 404L
      return(list(error = "No data found"))
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
