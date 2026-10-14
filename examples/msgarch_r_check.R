# Cross-check of src/regimes/msgarch.py against the R MSGARCH package (Ardia et al. 2019).
#
#   Rscript examples/msgarch_r_check.R tests/data/msgarch_sim.csv
#
# Fits a two-regime GJR-GARCH with normal and Student-t innovations and prints the log-likelihood and
# parameters at full precision; tests/test_msgarch.py checks the Python likelihood at these parameters.
# MSGARCH uses the first return only to start the variance recursions (it is not scored and does not
# update the regime probabilities), so the Python side reproduces that convention for the comparison.
suppressMessages(library(MSGARCH))
x <- read.csv(commandArgs(trailingOnly = TRUE)[1])[, 1]
for (d in c("norm", "std")) {
  spec <- CreateSpec(variance.spec = list(model = c("gjrGARCH")),
                     distribution.spec = list(distribution = c(d)),
                     switch.spec = list(do.mix = FALSE, K = 2))
  set.seed(0)
  fit <- FitML(spec, data = x, ctr = list(do.se = FALSE))
  cat("#####", d, "loglik", sprintf("%.6f", fit$loglik), "\n")
  cat(paste(names(fit$par), sprintf("%.12g", fit$par), collapse = "\n"), "\n")
}
