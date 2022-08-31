---
title: Challenges and weakness
category: Milestones and Results
order: 1
---

> Monitoring & Logging was not implemented yet!

The lack of data is definitely a bottleneck to our project. For example, within the initial data exploration a few rental types were found:

- DUB-General
- Workshop
- Healthcare
- Private

_`Workshop`_ is unknown if bikes were allocated either to an specific event or the workshop is provided by Moby Bikes in order to promote its services, for example. The same rule applies to _`Healthcare`_ type.

## Rental's duration

**Period of use**

"5.1 Bikes should not be used for more than 19 consecutive hours, this is the maximum period of use." [General Terms and Conditions (“GTC”)](https://app.mobymove.com/t-c.html)

> **Assumption**: Due to lack of information and data, to calculate the duration rental time I am assuming that when a new bike rental starts the duration in _minutes_ will be calculated by:

$$ (RentalDuration = LastGPSTime − LastRentalStart) $$


## Weather Data

### Phoenix Park Station vs Dublin Airport Station

Geographically, the station at Phoenix Park would be the most suitable choice but unfortunately, they do not collect Wind information which in Ireland plays an important role when deciding to go cycling or not. For those who are not familiar with Irish weather, it rains a lot and mostly we do not have much choice about it but the wind is something that can prevent you go outside or choosing a different kind of transportation. Heavy rain is not that common, though.

### Hourly vs Daily data

A daily data to the business could make more sense but because the weather is so unpredictable in Ireland (it can completely change in an hour), the best option would be hourly data if looking at a historical perspective. Important to note that from the Weather API the forecast is provided hourly. For simplicity and better planning, we can always aggregate the predicted results by day.
