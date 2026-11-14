# Predictor training report

Generated 2026-11-14 by `scripts/train_predictors.py`. All scores are on held-out test days (grouped CV). Baselines use training folds only.

## P3: Will a gas flame ignite?

Rows 177 (dropped 0 with missing inputs) · CV: leave-one-group-out (11 groups)
Classes: ignited 132, no ignition 45

| | accuracy | balanced_accuracy | macro_f1 | log_loss | brier | roc_auc |
|---|---|---|---|---|---|---|
| baseline | 0.7458 | 0.5 | 0.4272 | 0.6086 | 0.4091 | None |
| linear | 0.791 | 0.6694 | 0.687 | 0.5156 | 0.3168 | 0.7482 |
| boosting | 0.7401 | 0.5621 | 0.5613 | 0.6849 | 0.4317 | 0.7434 |
| linear plain inputs (no Tad, Zst) (n=177) | 0.7345 | 0.5217 | 0.4941 | 0.776 | 0.4464 | 0.4864 |
| linear NASA's Tad, Zst columns (n=177) | 0.791 | 0.6694 | 0.687 | 0.5077 | 0.3138 | 0.7558 |

Boosting clearly wins: **False**

Confusion (linear, held-out):

```
predicted    ignited  no ignition
actual                           
ignited          121           11
no ignition       26           19
```

## P4: Once lit, does a gas flame go out by itself?

Rows 132 (dropped 0 with missing inputs) · CV: leave-one-group-out (11 groups)
Classes: went out by itself 102, kept burning 30

| | accuracy | balanced_accuracy | macro_f1 | log_loss | brier | roc_auc |
|---|---|---|---|---|---|---|
| baseline | 0.7727 | 0.5 | 0.4359 | 0.5473 | 0.3594 | None |
| linear | 0.7727 | 0.6294 | 0.6408 | 0.4296 | 0.2516 | 0.8284 |
| boosting | 0.7955 | 0.6794 | 0.69 | 0.572 | 0.3398 | 0.7131 |
| linear + estimated Tad, Zst (n=132) | 0.7879 | 0.6627 | 0.6741 | 0.4353 | 0.2549 | 0.8261 |

Boosting clearly wins: **False**

Confusion (linear, held-out):

```
predicted           kept burning  went out by itself
actual                                              
kept burning                  11                  19
went out by itself            11                  91
```

## P1: How does a droplet fire end?

Rows 273 (dropped 0 with missing inputs) · CV: 10-fold grouped (80 groups)
Classes: extinction 185, disruption 61, completion 27

| | accuracy | balanced_accuracy | macro_f1 | log_loss | brier | roc_auc |
|---|---|---|---|---|---|---|
| baseline | 0.6777 | 0.3333 | 0.2693 | 0.8478 | 0.4933 | None |
| linear | 0.7436 | 0.483 | 0.4703 | 0.635 | 0.3492 | 0.7695 |
| boosting | 0.6996 | 0.4357 | 0.4282 | 0.7001 | 0.3886 | 0.7413 |
| linear +droplet size (n=261) | 0.7893 | 0.5284 | 0.5313 | 0.6366 | 0.341 | 0.7886 |

Boosting clearly wins: **False**

Confusion (linear, held-out):

```
predicted   completion  disruption  extinction
actual                                        
completion           0           7          20
disruption           0          32          29
extinction           1          13         171
```

## P1b: Does a droplet fire go out early?

Rows 273 (dropped 0 with missing inputs) · CV: 10-fold grouped (80 groups)
Classes: went out early 185, burned on 88

| | accuracy | balanced_accuracy | macro_f1 | log_loss | brier | roc_auc |
|---|---|---|---|---|---|---|
| baseline | 0.6777 | 0.5 | 0.4039 | 0.6453 | 0.4513 | None |
| linear | 0.8059 | 0.7584 | 0.7682 | 0.433 | 0.2831 | 0.8488 |
| boosting | 0.7729 | 0.7043 | 0.7174 | 0.4902 | 0.3194 | 0.8075 |

Boosting clearly wins: **False**

Confusion (linear, held-out):

```
predicted       burned on  went out early
actual                                   
burned on              55              33
went out early         20             165
```

## P2: Droplet burn time

Rows 259 (dropped 14 with missing inputs) · CV: 10-fold grouped (80 groups)

| | mae | rmse | r2 |
|---|---|---|---|
| baseline | 6.005 | 8.0994 | -0.1474 |
| linear | 3.3945 | 4.5948 | 0.6307 |
| boosting | 3.5784 | 4.9541 | 0.5707 |
| linear no fuel-specific slopes, no O2^2 (n=259) | 4.4699 | 6.2303 | 0.3211 |

Boosting clearly wins: **False**
80% range from held-out errors: [0.5766, 1.7831] (ratio to prediction)

## P5: Hot-flame burn time

Rows 143 (dropped 3 with missing inputs) · CV: 10-fold grouped (40 groups)

| | mae | rmse | r2 |
|---|---|---|---|
| baseline | 3.153 | 3.9004 | -0.0727 |
| linear | 1.0121 | 1.5374 | 0.8333 |
| boosting | 1.1323 | 1.7427 | 0.7859 |
| linear log pressure only (n=143) | 1.2845 | 1.882 | 0.7502 |

Boosting clearly wins: **False**
80% range from held-out errors: [0.8514, 1.2058] (ratio to prediction)

## P6: Hot-flame extinction diameter

Rows 141 (dropped 5 with missing inputs) · CV: 10-fold grouped (40 groups)

| | mae | rmse | r2 |
|---|---|---|---|
| baseline | 0.6404 | 0.7688 | -0.0245 |
| linear | 0.1365 | 0.2118 | 0.9223 |
| boosting | 0.1448 | 0.2335 | 0.9055 |

Boosting clearly wins: **False**
80% range from held-out errors: [-0.1886, 0.1857] (added to prediction)

## P6b: Hot-flame extinction diameter / initial droplet size

Rows 141 (dropped 5 with missing inputs) · CV: 10-fold grouped (40 groups)

| | mae | rmse | r2 |
|---|---|---|---|
| baseline | 0.0476 | 0.0645 | -0.0366 |
| linear | 0.0306 | 0.0473 | 0.4411 |
| boosting | 0.0279 | 0.0496 | 0.3866 |

Boosting clearly wins: **False**
80% range from held-out errors: [-0.0453, 0.0375] (added to prediction)

## P7: Cool-flame end state

Rows 117 (dropped 29 with missing inputs) · CV: 10-fold grouped (39 groups)
Classes: cool flame went out early 69, cool flame consumed the droplet 48

| | accuracy | balanced_accuracy | macro_f1 | log_loss | brier | roc_auc |
|---|---|---|---|---|---|---|
| baseline | 0.5897 | 0.5 | 0.371 | 0.6914 | 0.4979 | None |
| linear | 0.7949 | 0.7912 | 0.7893 | 0.4286 | 0.283 | 0.8736 |
| boosting | 0.7949 | 0.7754 | 0.7814 | 0.4613 | 0.2975 | 0.8729 |

Boosting clearly wins: **False**

Confusion (linear, held-out):

```
predicted                        cool flame consumed the droplet  cool flame went out early
actual                                                                                     
cool flame consumed the droplet                               37                         11
cool flame went out early                                     13                         56
```

## P8: Will the flame reignite?

Rows 145 (dropped 1 with missing inputs) · CV: 10-fold grouped (40 groups)
Classes: no reignition 110, reignited 35

| | accuracy | balanced_accuracy | macro_f1 | log_loss | brier | roc_auc |
|---|---|---|---|---|---|---|
| baseline | 0.7586 | 0.5 | 0.4314 | 0.5774 | 0.3841 | None |
| linear | 0.7931 | 0.7175 | 0.7175 | 0.3381 | 0.2288 | 0.8918 |
| boosting | 0.7448 | 0.6468 | 0.6482 | 0.4062 | 0.2803 | 0.8651 |

Boosting clearly wins: **False**

Confusion (linear, held-out):

```
predicted      no reignition  reignited
actual                                 
no reignition             95         15
reignited                 15         20
```
