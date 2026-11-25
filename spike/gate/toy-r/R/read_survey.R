#' Read the toy household survey
#'
#' @param path Path to a CSV file with columns `hhid`, `welfare` and `weight`.
#'   Defaults to the synthetic survey shipped with the package.
#' @return A data.table with one row per household.
#' @export
read_survey <- function(path = system.file("extdata", "survey.csv", package = "toypov")) {
  dt <- fread(path)
  needed <- c("hhid", "welfare", "weight")
  missing_cols <- setdiff(needed, names(dt))
  if (length(missing_cols) > 0) {
    stop("survey is missing columns: ", paste(missing_cols, collapse = ", "))
  }
  if (anyNA(dt$welfare) || any(dt$welfare <= 0)) {
    stop("welfare must be present and positive for every household")
  }
  if (anyNA(dt$weight) || any(dt$weight <= 0)) {
    stop("weight must be present and positive for every household")
  }
  if (anyDuplicated(dt$hhid) > 0) {
    stop("hhid must be unique")
  }
  return(dt)
}
