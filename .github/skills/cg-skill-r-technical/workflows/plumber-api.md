# Plumber APIs

Build REST APIs in R using `plumber`. Covers router setup, endpoint annotations, error handling, authentication, and deployment.

## Basic Router Setup

### Annotation-Based (Traditional)

Create a file `plumber.R` with endpoint annotations:

```r
# plumber.R

#* Health check
#* @get /health
function() {
  list(status = "ok", timestamp = Sys.time())
}

#* Get poverty data for a country
#* @param country_code ISO3 country code
#* @param year Survey year
#* @get /poverty/<country_code>/<year>
function(country_code, year) {
  year <- as.integer(year)
  dt <- load_poverty_data(country_code, year)

  if (nrow(dt) == 0) {
    stop("No data found for ", country_code, " in ", year)
  }

  list(
    country = country_code,
    year    = year,
    data    = as.list(dt)
  )
}

#* Calculate FGT indices for given parameters
#* @param country_code ISO3 country code
#* @param year Survey year
#* @param poverty_line Poverty line in 2017 PPP USD
#* @post /fgt
#* @serializer json
function(country_code, year, poverty_line = 2.15) {
  year <- as.integer(year)
  poverty_line <- as.numeric(poverty_line)

  result <- compute_fgt(country_code, year, poverty_line)

  list(
    country      = country_code,
    year         = year,
    poverty_line = poverty_line,
    fgt0         = result$fgt0,
    fgt1         = result$fgt1,
    fgt2         = result$fgt2
  )
}
```

Run the API:

```r
library(plumber)
pr("plumber.R") |> pr_run(port = 8080)
```

### Programmatic Router (Preferred for Complex APIs)

```r
# api.R
library(plumber)

pr() |>
  pr_get("/health", function() {
    list(status = "ok", timestamp = Sys.time())
  }) |>
  pr_get("/poverty/:country_code/:year", function(country_code, year) {
    year <- as.integer(year)
    dt <- load_poverty_data(country_code, year)
    list(country = country_code, year = year, data = as.list(dt))
  }) |>
  pr_post("/fgt", function(req, res) {
    body <- req$body
    result <- compute_fgt(body$country_code, body$year, body$poverty_line)
    result
  }) |>
  pr_run(port = 8080)
```

## Input and Output Types

### Path Parameters

```r
#* @get /country/<code>
function(code) {
  # code is always a character string
  # Validate it
  if (!grepl("^[A-Z]{3}$", code)) {
    stop("Invalid country code: ", code)
  }
  get_country(code)
}
```

### Query Parameters

```r
#* @get /search
function(region = NULL, year = NULL, limit = 100) {
  # Query params arrive as strings — convert types explicitly
  if (!is.null(year)) year <- as.integer(year)
  limit <- as.integer(limit)

  search_data(region = region, year = year, limit = limit)
}
```

### Request Body (POST)

```r
#* @post /calculate
#* @serializer json
function(req) {
  body <- req$body
  # body is a parsed list from the JSON request body
  compute_result(
    country = body$country,
    year    = as.integer(body$year),
    params  = body$params
  )
}
```

### Serializers

```r
#* Return JSON (default)
#* @serializer json
function() { list(a = 1) }

#* Return CSV
#* @serializer csv
function() { dt }

#* Return a plot as PNG
#* @serializer png list(width = 800, height = 600)
function() {
  plot(1:10)
}
```

## Error Handling

### Global Error Handler with pr_set_error()

```r
pr() |>
  pr_set_error(function(req, res, err) {
    # Log the error
    message("API Error: ", conditionMessage(err))

    # Return a structured error response
    res$status <- 500L
    list(
      error   = "Internal Server Error",
      message = conditionMessage(err)
    )
  }) |>
  pr_get("/data", function() {
    # If this throws, the error handler catches it
    load_data()
  }) |>
  pr_run(port = 8080)
```

### Endpoint-Level Error Handling

```r
#* @get /poverty/<code>
function(code, res) {
  tryCatch(
    {
      dt <- load_poverty_data(code)
      if (nrow(dt) == 0) {
        res$status <- 404L
        return(list(error = "Not Found",
                    message = paste("No data for", code)))
      }
      list(data = as.list(dt))
    },
    error = function(e) {
      res$status <- 500L
      list(error = "Server Error", message = conditionMessage(e))
    }
  )
}
```

## Authentication Filter

```r
# Authentication filter — runs before every endpoint
auth_filter <- function(req, res) {
  # Skip auth for health check

  if (req$PATH_INFO == "/health") {
    return(plumber::forward())
  }

  token <- req$HTTP_AUTHORIZATION
  if (is.null(token) || !validate_token(token)) {
    res$status <- 401L
    return(list(error = "Unauthorized", message = "Invalid or missing token"))
  }

  plumber::forward()
}

pr() |>
  pr_filter("auth", auth_filter) |>
  pr_get("/health", function() list(status = "ok")) |>
  pr_get("/data", function() load_data()) |>
  pr_run(port = 8080)
```

## OpenAPI Spec Generation

Plumber auto-generates an OpenAPI (Swagger) specification for your API:

```r
# Customize the spec
pr() |>
  pr_set_api_spec(function(spec) {
    spec$info$title <- "GPID Poverty Data API"
    spec$info$version <- "1.0.0"
    spec$info$description <- "Access poverty and inequality indicators"
    spec
  }) |>
  pr_get("/poverty/:code", function(code) { ... },
         preempt = "auth") |>
  pr_run(port = 8080)
```

The Swagger UI is available at `http://localhost:8080/__docs__/` when the API is running.

## CORS for Browser Access

```r
# Enable CORS for all origins (development only)
cors_filter <- function(req, res) {
  res$setHeader("Access-Control-Allow-Origin", "*")
  res$setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
  res$setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization")

  if (req$REQUEST_METHOD == "OPTIONS") {
    res$status <- 200L
    return(list())
  }

  plumber::forward()
}

pr() |>
  pr_filter("cors", cors_filter) |>
  ...
```

## Deployment

### Running with pr_run()

```r
# Development
pr("plumber.R") |> pr_run(port = 8080, host = "127.0.0.1")

# Production (listen on all interfaces)
pr("plumber.R") |> pr_run(port = 8080, host = "0.0.0.0")
```

### Deployment to Posit Connect

```r
# Deploy from RStudio/Positron
rsconnect::deployAPI(
  api     = "plumber.R",
  appName = "gpid-poverty-api",
  server  = "connect.example.com",
  account = "your-account"
)
```

Ensure `renv.lock` is committed — Connect uses it to rebuild the environment.

## Project Structure for Plumber APIs

```
api-project/
├── plumber.R             # API endpoint definitions
├── R/
│   ├── data.R            # Data loading functions
│   ├── compute.R         # Business logic
│   └── helpers.R         # Utility functions
├── tests/
│   └── testthat/
│       ├── test-endpoints.R
│       └── test-compute.R
├── data/                 # Reference data (small only)
├── DESCRIPTION           # If treating as a package
├── renv.lock
├── .gitignore
└── README.md
```
