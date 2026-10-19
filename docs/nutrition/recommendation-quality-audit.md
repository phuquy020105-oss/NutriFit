# Nutrition ranking and catalogue audit — 2026-10-19

## Reproduce

Run `mvn -Dtest=RealCatalogBenchmarkTest test` with JDK 21. The test reads the committed JSON verbatim, calls NutritionCalculator and the production ranking service through read-only in-memory ports, and writes `target/nutrition-audit/benchmark.csv` and a summary. No database connection, seed or user-data changes are made. The old policy is reproduced from commit a3ab60b: 10%-of-target calorie band, LIKE count, energy distance, meal balance, recipe IDs.

The 120 cases cover the five existing activity factors and lose/maintain/gain targets for a 30-year-old male, 70 kg, 175 cm; Free, Premium without preferences, Premium LIKE lean chicken and Premium DISLIKE fatty pork; empty journal or one historical half-serving of R023. Targets are fixed outputs of the existing OnboardingService, not a new BMR/TDEE implementation. No effectiveness or clinical claims are inferred from these offline cases.

Catalogue SHA-256: `419fa5e4ec57cabecf692dfe827ab764e564bb1bc76b0202f716bc669f23e685`.

## Ranking

All eligible breakfast/lunch/dinner combinations are considered, with fixed 1.00 serving. DISLIKE is a hard exclusion. Every soft component is normalized to [0,1], and lower total cost is better:

| Component | Weight | Definition |
|---|---:|---|
| Energy | 0.30 | Smooth relative projected-day error e/(0.20+e); 1.15 directional penalty for lose overshoot or gain shortfall |
| Protein | 0.08 | Distance outside 10–35% energy, normalized by interval width |
| Carbohydrate | 0.10 | Distance outside 45–65% energy |
| Fat | 0.15 | Distance outside 20–35% energy |
| Fiber | 0.17 | Remaining fraction of 14 g per 1,000 target kcal |
| Meal balance | 0.05 | Soft deviation from 25/40/35 shares, no exact per-meal target |
| Ingredient diversity | 0.06 | Mean weighted Jaccard overlap; common ingredients have inverse-frequency weight |
| Repetition | 0.06 | Recipes already recorded today or in the last five preview combinations |
| Premium LIKE | 0.03 | Fraction of unique liked foods not covered; never a hard requirement |

Reference ranges are adult soft ranking references from [Health Canada](https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-macronutrients.html), not medical prescriptions. Goal changes energy direction only; it does not invent goal-specific protein targets. Free/expired Premium do not read stored preferences. Regeneration prefers a novel menu only within 0.03 total cost of the current best. Ties resolve deterministically by energy error and recipe IDs. The 60-candidate performance test only clones the real 30 inputs in memory; these are explicitly capacity fixtures, not new recipes.

Projected totals use today's stored snapshots and the existing duplicate-merge calculation. They do not rewrite history. Saving still rechecks all recipes, ownership, current Premium/preferences, target and journal inside the existing atomic transaction.

## Benchmark result

115/120 cases changed, all 115 improved the documented combined cost; the remaining five tied. This is an objective-function comparison, not proof that source nutrients are laboratory measurements. Rows in the CSV include all five raw projected nutrients and energy difference. Larger calorie errors are an explicit tradeoff for less excessive fat and more fiber; no serving is scaled to disguise the gap.

| Metric (120 cases) | Old | New |
|---|---:|---:|
| Mean projected kcal | 1873.7961 | 1662.5676 |
| Mean protein g | 75.1225 | 95.7066 |
| Mean carbohydrate g | 186.4873 | 193.6017 |
| Mean fat g | 88.4367 | 52.7229 |
| Mean fiber g | 7.3074 | 12.5720 |
| Mean absolute calorie error | 682.6120 | 893.0629 |
| Cases above 35% fat energy | 87.0000 | 2.0000 |
| Cases reaching 14 g fiber / 1,000 actual kcal | 0.0000 | 0.0000 |
| Mean combined cost | 0.4068 | 0.2881 |

## Catalogue limits and expansion decision

All 82 foods remain ESTIMATED: zero have all five nutrients verified from a matched source record. Four have partial Vietnamese Food Composition Table 2007 references for kcal/P/C/F, with fiber still estimated. The other 78 use documented estimates. See [nutrient provenance](vietnamese-food-nutrition-data.md) and [ingredient/state/gram design](vietnamese-food-catalog-review.md). Numbers already present in MySQL are not treated as verification.

The 1,000 unfiltered three-meal combinations span 1034.335–1834.780 kcal. Maximum fiber is 13.229 g; maximum fiber density is 9.029 g/1,000 kcal. None reaches the 14 g reference. Thus the current fixed-serving catalogue cannot provide a balanced full day for many higher targets. The new algorithm improves selection but cannot create missing nutrients or energy.

**Expansion is needed, but no new 30 recipes are imported in this change.** The official USDA FoodData Central bulk/API hosts could not be resolved from this environment during source-record verification. The accessible dataset index alone does not verify a food's raw/cooked state, edible mass and all five nutrients. Adding 30 unverified recipes would violate the requested source gate. Next step: obtain a verified USDA SR Legacy/Foundation dataset, match individual foods and preparation states, review realistic edible grams/oil retention, then benchmark and import exactly 10 recipes per meal with a separate approved migration. Existing 30 names, grams and nutrients are unchanged.

One-serving gram totals below are edible components, including broth and water. A high soup total does not imply excessive solid food. Rice/noodles and meat are explicitly cooked where their food names say so; raw ingredients stay raw inputs, and retained oil is the amount in the recipe, not total fryer oil. No raw/cooked substitutions or nutrient corrections were made. Higher-fat meals include pork belly/egg R013 and fatty pork R022; leaner/high-protein choices include chicken rice R018, beef rice R017 and shrimp rice R026. Vegetable/legume choices R023 and R025 give more fiber, but remain insufficient for a whole day. Shared rice, fish sauce, salt and oil reduce apparent variety; inverse-frequency overlap avoids treating these staples like distinctive protein/vegetable ingredients.

## Per-recipe audit (NutritionCalculator, 1.00 serving)

| Ref | Dish | Meal | kcal | Protein g | Carbs g | Fat g | Fiber g | Ingredient count | Edible input g (including liquids) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| R001 | Phở bò | BREAKFAST | 456.290 | 34.613 | 50.045 | 11.670 | 1.842 | 12 | 629.20 |
| R002 | Phở gà | BREAKFAST | 420.100 | 37.663 | 50.055 | 5.940 | 1.844 | 12 | 628.20 |
| R003 | Bánh mì trứng | BREAKFAST | 427.840 | 20.698 | 46.815 | 17.017 | 2.779 | 11 | 253.50 |
| R004 | Bún bò Huế | BREAKFAST | 509.330 | 38.853 | 50.748 | 14.674 | 2.068 | 15 | 648.00 |
| R005 | Hủ tiếu Nam Vang | BREAKFAST | 465.950 | 38.235 | 45.835 | 12.977 | 2.007 | 15 | 638.20 |
| R006 | Cháo gà | BREAKFAST | 293.770 | 25.083 | 32.712 | 5.891 | 0.836 | 11 | 481.70 |
| R007 | Bánh cuốn | BREAKFAST | 424.420 | 21.700 | 55.643 | 11.943 | 1.577 | 14 | 351.00 |
| R008 | Bún riêu | BREAKFAST | 426.840 | 27.480 | 52.945 | 10.442 | 3.670 | 15 | 730.00 |
| R009 | Xôi gà | BREAKFAST | 533.950 | 27.120 | 66.345 | 16.717 | 2.240 | 11 | 325.20 |
| R010 | Bánh canh cua | BREAKFAST | 374.380 | 22.918 | 52.305 | 7.250 | 0.900 | 12 | 587.20 |
| R011 | Cơm tấm sườn | LUNCH | 645.275 | 31.712 | 66.585 | 26.805 | 2.554 | 16 | 481.30 |
| R012 | Cơm gà xối mỡ | LUNCH | 635.260 | 36.343 | 53.302 | 29.560 | 2.062 | 13 | 456.50 |
| R013 | Cơm thịt kho trứng | LUNCH | 666.855 | 18.912 | 51.588 | 41.627 | 1.270 | 12 | 413.30 |
| R014 | Cơm cá kho tộ | LUNCH | 372.345 | 26.377 | 50.778 | 6.555 | 1.352 | 11 | 369.50 |
| R015 | Bún chả Hà Nội | LUNCH | 539.965 | 33.559 | 55.585 | 18.881 | 2.951 | 16 | 474.30 |
| R016 | Bún thịt nướng | LUNCH | 608.100 | 33.679 | 58.105 | 25.964 | 3.946 | 18 | 500.00 |
| R017 | Cơm bò lúc lắc | LUNCH | 554.375 | 36.030 | 53.820 | 19.875 | 3.524 | 12 | 441.30 |
| R018 | Cơm gà luộc | LUNCH | 439.880 | 36.946 | 52.606 | 7.276 | 1.698 | 13 | 400.30 |
| R019 | Cơm sườn ram | LUNCH | 568.365 | 31.092 | 51.668 | 25.672 | 1.811 | 13 | 414.30 |
| R020 | Cơm cá chiên | LUNCH | 466.290 | 34.430 | 50.120 | 13.427 | 1.898 | 12 | 439.20 |
| R021 | Cơm cá hấp | DINNER | 368.220 | 28.974 | 48.871 | 5.840 | 1.755 | 12 | 392.20 |
| R022 | Cơm thịt rang | DINNER | 633.975 | 13.427 | 49.978 | 41.358 | 1.352 | 10 | 339.30 |
| R023 | Cơm canh chua cá | DINNER | 437.150 | 28.930 | 64.540 | 5.947 | 5.613 | 16 | 752.30 |
| R024 | Cơm gà kho gừng | DINNER | 467.900 | 33.979 | 50.066 | 13.409 | 1.557 | 12 | 396.20 |
| R025 | Cơm đậu hũ sốt cà | DINNER | 489.560 | 22.960 | 57.195 | 17.882 | 4.393 | 13 | 587.70 |
| R026 | Cơm tôm rim | DINNER | 398.910 | 32.022 | 52.568 | 5.959 | 1.746 | 12 | 415.20 |
| R027 | Cơm thịt luộc | DINNER | 447.390 | 37.912 | 50.153 | 9.461 | 1.798 | 12 | 420.20 |
| R028 | Cơm canh bí đỏ | DINNER | 395.710 | 23.220 | 52.115 | 9.051 | 1.808 | 10 | 628.70 |
| R029 | Cơm cá kho | DINNER | 368.855 | 26.356 | 49.864 | 6.595 | 1.480 | 12 | 373.30 |
| R030 | Cơm trứng chiên | DINNER | 428.830 | 17.994 | 47.996 | 17.157 | 2.006 | 10 | 394.50 |

## Presentation and integrity

NutritionDisplay formats integer HALF_UP with Vietnamese grouping (`1693.655` → `1.694`, `-0.500` → `-1`). Each card, daily total, target and difference is rounded independently from its original BigDecimal. Three rounded cards may differ from the rounded raw total by one unit, and rounded difference may differ from subtraction of the displayed integers by one unit; the UI explains this. Database snapshots still have three decimals. History values, including earlier fractional servings, are never recalculated or rounded back into storage. There are no portion inputs in the Nutrition UI.

The read-only Aiven audit matched all 82 food nutrient rows, 30 recipe names/meal types/base servings and 383 ingredient/gram links to this JSON before image work. Only image_url is covered by the separate image migration. No additional foods, recipes, nutrient updates or schema changes are included.
