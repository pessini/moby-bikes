---
title: Data Pipeline
category: Minimum Viable Product (MVP)
order: 1
---

The chosen Data Pipeline structure was using AWS Services as showing below:

![Data Pipeline](https://github.com/pessini/moby-bikes/blob/73f3d0af24a09b91fb1ca3c3d09edbf66273fdbf/documentation/data-pipeline.png?raw=true)

## Summary

- Every morning a Lambda function is invoked to pull data from APIs and dump it into a S3 Bucket.

- Later in the morning, a new Lambda function is invoked to parse files from S3, process and load them into an Aurora (MySQL) database.

- A [Streamlit web app](https://pessini-moby-bikes-dashboardapp-hhvohw.streamlitapp.com/) is deployed to present an analytical dashboard with KPIs and Rentals Demand predictions from Weather Forecast.