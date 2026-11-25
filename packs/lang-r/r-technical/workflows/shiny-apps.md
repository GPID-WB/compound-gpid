# Shiny Apps

Module-based Shiny applications. Use `collapse` for fast aggregation inside reactive expressions.

## Module Pattern

```r
mod_poverty_chart_ui <- function(id) {
  ns <- NS(id)
  tagList(
    selectInput(ns("region"), "Region", choices = c("All", "EAP", "SSA")),
    plotOutput(ns("chart"), height = "400px")
  )
}

mod_poverty_chart_server <- function(id, data) {
  moduleServer(id, function(input, output, session) {
    filtered <- reactive({
      dt <- data()
      if (input$region != "All") dt <- dt[region == input$region]
      dt
    })

    output$chart <- renderPlot({
      req(fnrow(filtered()) > 0)
      # Aggregate with collapse before plotting
      agg <- collap(filtered(), ~ year, fmean, w = ~ weight, cols = "headcount")
      ggplot(qDT(agg), aes(x = year, y = headcount)) +
        geom_line(linewidth = 1, lineend = "round") +
        theme_wb(chartType = "line")
    }) |> bindCache(input$region)
  })
}
```

## Key Patterns

- `ns()` for all input/output IDs inside modules
- `req()` for input validation (better than `if/return(NULL)`)
- `bindCache()` to cache expensive renders by input values
- `bindEvent()` to control when reactives fire
- `reactlog::reactlog_enable()` for debugging reactive chains
- **Static reference data** — load once at app startup in global scope (runs once, shared across all sessions):
  ```r
  # At the top of app.R (global scope)
  welfare_dt <- fread("data/welfare.parquet")
  setkey(welfare_dt, country, year)
  ```
  Reserve `reactive()` / `reactiveVal()` for data that varies by session or user input. Never re-read a static dataset inside a `reactive()` on every request.

## Testing Modules

```r
testServer(mod_poverty_chart_server,
  args = list(data = reactive({ test_dt })),
  { session$setInputs(region = "EAP")
    expect_true(fnrow(filtered()) > 0) })
```

## Project Structure

```
shiny-app/
├── app.R
├── R/mod_*.R
├── data/
├── www/
├── tests/testthat/
├── renv.lock
└── README.md
```

Deploy with `rsconnect::deployApp()`.
