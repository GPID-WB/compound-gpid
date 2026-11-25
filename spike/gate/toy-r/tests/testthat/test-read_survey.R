test_that("read_survey() reads the synthetic survey", {
  dt <- read_survey()
  expect_equal(nrow(dt), 20)
  expect_named(dt, c("hhid", "welfare", "weight"))
})

test_that("read_survey() refuses a non-positive weight", {
  path <- withr::local_tempfile(fileext = ".csv")
  writeLines(c("hhid,welfare,weight", "1,2.5,0"), path)
  expect_error(read_survey(path), "weight must be present and positive")
})
