# Shiny Apps

## Module Pattern (Required for Non-Trivial Apps)

```r
# R/mod_filter.R

# UI function — always takes `id` as first argument
mod_filter_ui <- function(id) {
  ns <- NS(id)                # namespace function
  tagList(
    selectInput(ns("country"), "Country", choices = NULL),
    sliderInput(ns("year"), "Year", min = 2000, max = 2023, value = 2020)
  )
}

# Server function — always takes `id` as first argument
mod_filter_server <- function(id, data) {
  moduleServer(id, function(input, output, session) {
    observe({
      updateSelectInput(session, "country",
                        choices = unique(data()$country))
    })

    # Return reactive values for parent to consume
    reactive({
      list(country = input$country, year = input$year)
    })
  })
}
```

## App Entry Point

```r
# app.R
library(shiny)

ui <- fluidPage(
  titlePanel("GPID Poverty Explorer"),
  sidebarLayout(
    sidebarPanel(
      mod_filter_ui("filters")
    ),
    mainPanel(
      plotOutput("poverty_plot"),
      tableOutput("poverty_table")
    )
  )
)

server <- function(input, output, session) {
  data <- reactive({ load_data() })

  filters <- mod_filter_server("filters", data)

  filtered <- reactive({
    data()[country == filters()$country & year == filters()$year]
  })

  output$poverty_plot <- renderPlot({
    plot_poverty(filtered())
  })
}

shinyApp(ui, server)
```

## Reactivity Patterns

```r
# Reactive expression — caches result, re-runs when inputs change
processed <- reactive({
  heavy_computation(input$param)
})

# Observer — side effects only (no return value)
observe({
  cat("Input changed:", input$country, "\n")
})

# observeEvent — runs on specific trigger only
observeEvent(input$submit, {
  save_results(processed())
})

# eventReactive — like reactive() but triggered explicitly
result <- eventReactive(input$submit, {
  run_model(input$params)
})

# isolate — read reactive value without creating dependency
observeEvent(input$btn, {
  current <- isolate(input$slider)
  # ... use current without reactivity
})
```

## Namespace Rules

- Always use `ns()` inside module UI functions.
- Never use `ns()` inside module server functions — `moduleServer` handles it.
- Use `session$ns()` inside server if you need the namespace string explicitly.

## Performance

```r
# Cache expensive operations with bindCache()
output$big_plot <- renderPlot({
  make_plot(input$country)
}) |> bindCache(input$country)

# Use req() to guard against NULL inputs
filtered <- reactive({
  req(input$country)   # stops if NULL/empty/FALSE
  data()[country == input$country]
})
```

## Project Structure

```
my-app/
├── R/
│   ├── mod_filter.R      # Filter module
│   ├── mod_chart.R       # Chart module
│   └── utils.R           # Shared helpers
├── www/                  # Static assets (CSS, JS, images)
├── tests/
│   └── testthat/
│       └── test-utils.R  # Test non-reactive logic
├── app.R                 # Entry point
└── DESCRIPTION
```

Test non-reactive helper functions with `testthat`. For reactive logic, use `shinytest2`.
