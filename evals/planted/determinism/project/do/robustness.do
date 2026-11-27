* Bootstrap of the headcount ratio.
import delimited "data/survey.csv", clear
generate poor = welfare < 3
bootstrap r(mean), reps(200): summarize poor [aweight = weight]
