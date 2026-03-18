# Verify FGT(1) calculation
welfare <- c(1, 1.5, 2, 3, 5)
poverty_line <- 2.15

# Calculate gaps
gaps <- numeric(length(welfare))
for (i in seq_along(welfare)) {
  if (welfare[i] < poverty_line) {
    gaps[i] <- (poverty_line - welfare[i]) / poverty_line
  } else {
    gaps[i] <- 0
  }
}

cat("Welfare values:", welfare, "\n")
cat("Poverty line:", poverty_line, "\n")
cat("Gaps:", round(gaps, 6), "\n")
cat("Mean gap (FGT1):", round(mean(gaps), 10), "\n")
cat("\nDetailed breakdown:\n")
for (i in seq_along(welfare)) {
  if (welfare[i] < poverty_line) {
    cat(sprintf("HH %d: welfare=%.1f, gap=(%.2f-%.1f)/%.2f=%.10f\n", 
      i, welfare[i], poverty_line, welfare[i], poverty_line, gaps[i]))
  } else {
    cat(sprintf("HH %d: welfare=%.1f, gap=0 (not poor)\n", i, welfare[i]))
  }
}

# Verify what the test expects
expected_gaps <- c(1.15, 0.65, 0.15, 0, 0) / 2.15
expected_mean <- mean(expected_gaps)
cat("\nTest's expected breakdown:\n")
cat("Gaps as shown in test: (1.15, 0.65, 0.15, 0, 0) / 2.15\n")
cat("Test's expected mean:", round(expected_mean, 10), "\n")
cat("Match?", all.equal(mean(gaps), expected_mean), "\n")
