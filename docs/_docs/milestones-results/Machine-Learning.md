---
title: Machine Learning
category: Milestones and Results
order: 3
---

## Notebooks

1. [Data Wrangling]({{ site.baseurl }}/notebooks-html/01-data-wrangling.html)
1. [Feature Engineering]({{ site.baseurl }}/notebooks-html/02-feature-engineering.html)
1. [Exploratory Data Analysis]({{ site.baseurl }}/notebooks-html/03-exploratory-data-analysis.html)
1. [Outlier Analysis]({{ site.baseurl }}/notebooks-html/03A-outliers.html)
1. [Linear Regression]({{ site.baseurl }}/notebooks-html/04A-linear-regression.html)
1. [Poisson Regression]({{ site.baseurl }}/notebooks-html/04B-poisson.html)
1. [Time Series Analysis]({{ site.baseurl }}/notebooks-html/04C-time-series.html)
1. [Modeling]({{ site.baseurl }}/notebooks-html/05-modeling.html)
1. [XGBoost]({{ site.baseurl }}/notebooks-html/06-xgboost-model.html)
1. [Model Evaluation]({{ site.baseurl }}/notebooks-html/07-evaluation.html)

<!-- **[Pre-trained XGBoost model](https://github.com/pessini/moby-bikes/blob/main/dashboard/xgb_pipeline.pkl)** -->

## Experiment Tracker

The Data Pipeline was deployed using a combination of AWS services and Streamlit. To delivery predictions, several notebooks were created such as feature engineering and XGBoost modeling to achieve a **Normalized Root Mean Square Error (NRMSE)** of *0.14699*

To keep track of different models tested, an[ Excel file](https://github.com/pessini/moby-bikes/blob/main/documentation/experiment_tracker.xlsx) is created (with help of a [Python class](https://gist.github.com/pessini/32227430c700a081acc608725dee4eb7) to document all versions.

[Experiment Tracker Class](https://gist.github.com/pessini/32227430c700a081acc608725dee4eb7)

| ![Experiment Tracker - Ideas]({{ site.baseurl }}/images/exp_tracker_ideas.png) |
| :--: |
| *Experiment Tracker - Sheet Ideas* |

| ![Experiment Tracker - Experiments]({{ site.baseurl }}/images/exp_tracker.png) |
|:--:|
| *Experiment Tracker - Sheet Experiments* |

> After [Exploratory]({{ site.baseurl }}/notebooks-html/03-exploratory-data-analysis.html), [Outlier]({{ site.baseurl }}/notebooks-html/03A-outliers.html), and [Time Series]({{ site.baseurl }}/notebooks-html/04C-time-series.html) Analyses, it was decided that **Decision Tree** learning algorithm was chosen as primary model type for the experiments.

## Modeling

Different supervised algorithms were tested with little feature engineering and XGBoost yields the best results. Check out the [Notebook]({{ site.baseurl }}/notebooks-html/05-modeling.html).

| ![Feature Importances]({{ site.baseurl }}/images/feature_importances.png) |
| :--: |
| *Feature Importances Plot from XGBoost model* |

Several XGBoost models were built and logged with Experiment Tracker Class mentioned above. [XGBoost Tracker](https://github.com/pessini/moby-bikes/blob/b7dfa5b415b4651dc70f892d05681d45983fbf38/documentation/experiment_tracker_xgboost.xlsx)

## Evaluation

Normalized Root Mean Square Error (NRMSE) was the main metric used to evaluate and compare the models.

$$ NRMSE = \frac{RSME}{y_{max} - y_{min}} $$

---

| ![Daily Rentals Prediction Plot]({{ site.baseurl }}/images/actual_predicted_daily.png) |
| :--: |
| *Daily Rentals Prediction Plot* |
