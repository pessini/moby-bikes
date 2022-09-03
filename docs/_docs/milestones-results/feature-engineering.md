---
title: Feature Engineering
category: Milestones and Results
order: 2
---

## Hypothesis

Hourly trend: It might be a high demand for people commuting to work. Early morning and late evening can have different trend (cyclist) and low demand during 10:00 pm to 4:00 am.

Daily Trend: Users demand more bike on weekdays as compared to weekend or holiday.

Rain: The demand of bikes will be lower on a rainy day as compared to a sunny day. Similarly, higher humidity will cause to lower the demand and vice versa.

Temperature: In Ireland, temperature has positive correlation with bike demand.

Traffic: It can be positively correlated with Bike demand. Higher traffic may force people to use bike as compared to other road transport medium like car, taxi etc.

## Date and time - new features
- `holiday`
- `workingday`
- `peak`
- `season`: (1 = Spring, 2 = Summer, 3 = Fall, 4 = Winter)
- `duration`: duration of the rental

## Times of the Day
- Morning (from 7am to noon)
- Afternoon (from midday to 6pm)
- Evening (from 6pm to 10pm)
- Night (from 10pm to 5am)

## Rainfall Intensity Level

| Level | Rainfall Intensity |
| :- | :-: |
| no rain        | 0       |
| drizzle        | 0.1~0.3 |
| light rain     | 0.3~0.5 |
| moderate rain  | 0.5~4   |
| heavy rain     | >4      |

Source: [https://www.metoffice.gov.uk/research/library-and-archive/publications/factsheets](https://www.metoffice.gov.uk/research/library-and-archive/publications/factsheets)

PDF direct link: [Water in the atmosphere](https://www.metoffice.gov.uk/binaries/content/assets/metofficegovuk/pdf/research/library-and-archive/library/publications/factsheets/factsheet_3-water-in-the-atmosphere-v02.pdf)

## Met Éireann Weather Forecast API

API URL: [https://data.gov.ie/dataset/met-eireann-weather-forecast-api/resource/5d156b15-38b8-4de9-921b-0ffc8704c88e](https://data.gov.ie/dataset/met-eireann-weather-forecast-api/resource/5d156b15-38b8-4de9-921b-0ffc8704c88e)

**Precipitation unit:** Rain will be output in *millimetres (mm)*.

The minvalue, value and maxvalue values are derived from statistical analysis of the forecast, and refer to the lower (20th percentile), middle (60th percentile) and higher (80th percentile) expected amount. If minvalue and maxvalue are not output, value is the basic forecast amount.

```html
<precipitation unit="mm" value="0.0" minvalue="0.0" maxvalue="0.1"/>
```

## Wind Speed Beaufort scale

[The Irish Meteorological Service - BEAUFORT SCALE](https://www.met.ie/forecasts/marine-inland-lakes/beaufort-scale)

![Beaufort scale](https://github.com/pessini/moby-bikes/blob/902858f47ba9afaf380abfc2be02a2b7f1f09174/notebooks/img/Beaufort-scale.png?raw=true)

Another source: [https://www.metoffice.gov.uk/weather/guides/coast-and-sea/beaufort-scale](https://www.metoffice.gov.uk/weather/guides/coast-and-sea/beaufort-scale)

## Grouped Wind Speed (Beaufort scale)

| Level | Beaufort scale |
| :- | :-: |
| Calm / Light Breeze           | 0~2     |
| Breeze                        | 3       |
| Moderate Breeze               | 4-5     |
| Strong Breeze / Near Gale     | 6-7     |
| Gale / Storm                  | 8~12    |


## Initial new features

#### Date/time
- Holiday
- Working Day (eg. weekend)
- Season (eg. Summer)
- Times of Day (eg. Morning)
- Day of the week (eg. Monday)

#### Weather
- Rainfall Intensity Level (eg. light rain)
- Wind Speed (Beaufort Scale)
- Wind Speed (grouped bft wind speed - helps high cardinality)
- Temperature round (eg. 16.7&deg;C -> 17&deg;C)
- Temperature Bins (clusters for different temperatures)
- Humidity Bins (clusters for different relative humidity levels)

*[See Feature Engineering Notebook]({{ site.baseurl }}/notebooks-html/02-feature-engineering.html)*
