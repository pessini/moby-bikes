---
title: Challenges and directions
category: Milestones and Results
order: 1
---

## Data Wrangling

[Jupyter Notebook]({{ site.baseurl }}/notebooks-html/01-data-wrangling.html)

### Moby API Data fields

- `HarvestTime` - Data retrieval timestamp
- `BikeID` - Unique bike ID used for rent bike
- `Battery` - Battery status (max distance in km)
- `BikeIdentifier` - Bike Identifier (Generally contains only digits, might contains chars)
- `BikeTypeName` - Bike type name
- `EBikeProfileID` - E-bike Profile ID (Every ebike profile has defined Geofence (allowed riding areas))
- `EBikeStateID` - EBike State (Indicates: {1:'Warning - is in move and not rented',2:'Normal',3:'Switched Off',4:'Firmware Upgrade',5:'Laying on the ground'})
- `IsEBike` - Is electronic bike (Bike sends messages to Backend if bike is equipped with electronic, bluetooth etc.)
- `IsMotor` - Bike has engine
- `IsSmartLock` - Bike has smart lock
- `LastGPSTime` - Last valid GPS message
- `LastRentalStart` - Last time bike was rented
- `Latitude` - Bike coordinates if bike is locked out of station
- `Longitude` - Bike coordinates if bike is locked out of station
- `SpikeID` - Might be used for rent bike instead of BikeID

The lack of data is definitely a bottleneck to our project. For example, within the initial data exploration a few rental types were found:

- DUB-General
- Workshop
- Healthcare
- Private

`Workshop` is related to events which bikes are allocated either to an specific time period or an event provided by Moby Bikes in order to promote its services.

Regarding `Healthcare` type, is a ebike scheme that was offered for free to frontline workers.

#### Rental's duration

**Period of use**

"5.1 Bikes should not be used for more than 19 consecutive hours, this is the maximum period of use." [General Terms and Conditions (“GTC”)](https://app.mobymove.com/t-c.html)

> **Assumption**: Due to lack of data, to calculate the duration rental time I am assuming that when a new bike rental starts the duration in _minutes_ will be calculated by:

$$ (RentalDuration = LastGPSTime − LastRentalStart) $$


### Weather Data - Met Éireann

Regarding the weather data there are two important decisions to deal with:

- One is about from which station the historical data will be collected;
- and the other one is about the frequency of data, which can be hourly or daily.

#### Phoenix Park Station vs Dublin Airport Station

Geographically, the station at Phoenix Park would be the most suitable choice but unfortunately, they do not collect Wind information which in Ireland plays an important role when deciding to go cycling or not. For those who are not familiar with Irish weather, it rains a lot and mostly we do not have much choice about it but the wind is something that can prevent you go outside or choosing a different kind of transportation. Heavy rain is not that common, though.

#### Hourly vs Daily data

A daily data to the business could make more sense but because the weather is so unpredictable in Ireland (it can completely change in an hour), the best option would be hourly data if looking at a historical perspective. Important to note that from the Weather API the forecast is provided hourly. For simplicity and better planning, we can always aggregate the predicted results by day.

**Dublin Airport (*Hourly Data*)**: [https://data.gov.ie/dataset/dublin-airport-hourly-data](https://data.gov.ie/dataset/dublin-airport-hourly-data)

> Monitoring & Logging was not implemented yet!
