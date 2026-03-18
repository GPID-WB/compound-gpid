# Shiny Apps

Building Shiny applications using the module pattern. Covers module architecture, namespacing, reactivity debugging, performance optimization, and deployment.

## Module Architecture

Every Shiny app beyond a simple prototype should use modules. Modules encapsulate UI and server logic, prevent ID collisions, and make the app testable.

### Module Pattern

```r
# R/mod_poverty_chart.R

#' Poverty Chart Module — UI
#'
#' @param id Module namespace ID
#' @export
mod_poverty_chart_ui <- function(id) {
  ns <- NS(id)

  tagList(
    selectInput(ns("region"), "Region",
                choices = c("All", "EAP", "ECA", "LAC", "MNA", "SAR", "SSA")),
    sliderInput(ns("year_range"), "Years",
                min = 2000, max = 2023, value = c(2010, 2023)),
    plotOutput(ns("chart"), height = "400px")
  )
}

#' Poverty Chart Module — Server
#'
#' @param id Module namespace ID
#' @param data Reactive data.table with poverty data
#' @export
mod_poverty_chart_server <- function(id, data) {
  moduleServer(id, function(input, output, session) {
    filtered_data <- reactive({
      dt <- data()
      if (input$region != "All") {
        dt <- dt[region == input$region]
      }
      dt[year >= input$year_range[1] & year <= input$year_range[2]]
    })

    output$chart <- renderPlot({
      req(nrow(filtered_data()) > 0)

      ggplot(filtered_data(), aes(x = year, y = headcount, color = country)) +
        geom_line(linewidth = 1, lineend = "round") +
        scale_color_wb_d() +
        labs(title = "Poverty Headcount Ratio",
             x = NULL, y = "Headcount (%)") +
        theme_wb(chartType = "line")
    })
  })
}
```

### Using Modules in the App

```r
# app.R
library(shiny)
library(data.table)
library(ggplot2)
library(wbplot)

# Source modules
source("R/mod_poverty_chart.R")
source("R/mod_data_table.R")

ui <- fluidPage(
  titlePanel("GPID Poverty Dashboard"),
  sidebarLayout(
    sidebarPanel(
      mod_filters_ui("filters")   # different module, different ID
    ),
    mainPanel(
      mod_poverty_chart_ui("poverty"),
      mod_data_table_ui("table")
    )
  )
)

server <- function(input, output, session) {
  # Shared reactive data
  poverty_data <- reactive({
    as.data.table(fread("data/poverty.csv"))
  })

  # Initialize modules — pass shared data
  mod_poverty_chart_server("poverty", data = poverty_data)
  mod_data_table_server("table", data = poverty_data)
}

shinyApp(ui, server)
```

## Namespacing with ns()

Every input and output ID inside a module must be wrapped with `ns()`. This prevents ID collisions when the same module is used multiple times.

```r
# WRONG — will collide if module is used twice
selectInput("region", "Region", choices = regions)

# RIGHT — namespaced
ns <- NS(id)
selectInput(ns("region"), "Region", choices = regions)
```

Inside `moduleServer()`, `input$region` automatically resolves to the namespaced ID. You do NOT use `ns()` when reading inputs in the server function.

## Input Validation with req()

`req()` silently stops reactive execution when a condition is not met. Use it to prevent errors from missing or invalid inputs.

```r
output$chart <- renderPlot({
  # Stop silently if no data
  req(input$region)
  req(nrow(filtered_data()) > 0)

  ggplot(filtered_data(), ...) + ...
})
```

`req()` is better than `if (...) return(NULL)` because it integrates with Shiny's reactivity system and shows a grayed-out state rather than an error.

## Performance

### bindCache() — Cache Expensive Computations

```r
output$chart <- renderPlot({
  req(filtered_data())
  ggplot(filtered_data(), aes(x = year, y = headcount)) +
    geom_line(lineend = "round") +
    theme_wb(chartType = "line")
}) |>
  bindCache(input$region, input$year_range)
```

`bindCache()` stores the rendered output keyed by the input values. If the user selects the same region and year range again, the cached result is returned instantly.

### bindEvent() — Control When Reactives Execute

```r
# Only recompute when the button is clicked, not on every input change
filtered_data <- reactive({
  dt <- raw_data()
  dt[region == input$region & year >= input$year_range[1]]
}) |>
  bindEvent(input$go_button)
```

### Avoid Reactive Bottlenecks

```r
# WRONG — reloads data every time any input changes
server <- function(input, output, session) {
  output$chart <- renderPlot({
    dt <- fread("big_file.csv")  # Reloads on every invalidation
    dt[region == input$region]
    ...
  })
}

# RIGHT — load once, filter reactively
server <- function(input, output, session) {
  raw_data <- reactive({ fread("big_file.csv") }) |> bindCache()

  filtered <- reactive({
    raw_data()[region == input$region]
  })

  output$chart <- renderPlot({
    ggplot(filtered(), ...) + ...
  })
}
```

## Reactivity Debugging with reactlog

When reactive chains produce unexpected behavior, use `reactlog` to visualize the dependency graph:

```r
# Enable logging (before running the app)
reactlog::reactlog_enable()

# Run the app
shinyApp(ui, server)

# After closing, view the log
reactlog::reactlog_show()
```

This produces an interactive visualization showing which reactives depend on which inputs and when they fire.

## Project Structure

```
shiny-app/
├── app.R                 # Main app file (or ui.R + server.R)
├── R/
│   ├── mod_poverty_chart.R
│   ├── mod_data_table.R
│   ├── mod_download.R
│   └── utils.R           # Shared helper functions
├── data/                 # Static data files
├── www/                  # Static web assets (CSS, images, JS)
│   └── styles.css
├── tests/
│   └── testthat/
│       ├── test-mod_poverty_chart.R
│       └── test-utils.R
├── DESCRIPTION           # Package metadata (for golem or rhino apps)
├── renv.lock
└── README.md
```

## Deployment

### Posit Connect

```r
rsconnect::deployApp(
  appDir  = ".",
  appName = "gpid-poverty-dashboard",
  server  = "connect.example.com",
  account = "your-account"
)
```

### shinyapps.io

```r
rsconnect::deployApp(
  appDir  = ".",
  appName = "gpid-poverty-dashboard"
)
```

For both platforms, ensure `renv.lock` is present so the deployment environment matches your development environment.

## Testing Modules

```r
# tests/testthat/test-mod_poverty_chart.R
library(shiny)
library(testthat)

test_that("poverty chart module filters data correctly", {
  testServer(mod_poverty_chart_server,
    args = list(data = reactive({
      data.table(
        region   = c("EAP", "SSA", "EAP"),
        year     = c(2020, 2020, 2021),
        headcount = c(1.2, 35.0, 1.0),
        country  = c("CHN", "NGA", "CHN")
      )
    })),
    {
      session$setInputs(region = "EAP", year_range = c(2020, 2021))

      expect_equal(nrow(filtered_data()), 2)
      expect_true(all(filtered_data()$region == "EAP"))
    }
  )
})
```
