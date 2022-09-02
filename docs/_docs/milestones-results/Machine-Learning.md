---
title: Machine Learning
category: Milestones and Results
order: 2
---

The Data Pipeline was deployed using a combination of AWS services and Streamlit. To delivery predictions, several notebooks were created such as feature engineering and XGBoost modeling to achieve a **Normalized Root Mean Square Error (NRMSE)** of 0.14699

To keep track of different models tested, an[ Excel file](https://github.com/pessini/moby-bikes/blob/main/documentation/experiment_tracker.xlsx) is created (with help of a [Python class](https://gist.github.com/pessini/32227430c700a081acc608725dee4eb7) to document all versions.

[Experiment Tracker Class](https://gist.github.com/pessini/32227430c700a081acc608725dee4eb7)

| ![Experiment Tracker - Ideas]({{ site.baseurl }}/images/exp_tracker_ideas.png) |
| :--: |
| *Experiment Tracker - Sheet Ideas* |

| ![Experiment Tracker - Experiments]({{ site.baseurl }}/images/exp_tracker.png) |
|:--:|
| *Experiment Tracker - Sheet Experiments* |

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

**Pre-trained XGBoost model**: [https://github.com/pessini/moby-bikes/blob/main/dashboard/xgb_pipeline.pkl](https://github.com/pessini/moby-bikes/blob/main/dashboard/xgb_pipeline.pkl)
