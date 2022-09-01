---
category: Research and Exploration
title: ""
order: 1
---
# APIs Sources

A few data sources were identified to supply the Data Pipeline and be used as main data for this project:

- [Moby Bikes](https://mobybikes.com/) has a [public API](https://data.smartdublin.ie/mobybikes-api) where it provides current locations of the bikes in operation in the Dublin area and is updated every 5 minutes. There are also rollups of historic bike location data (30 minutes granularity) available as downloadable CSV resources.
- The [Met Éireann](https://www.met.ie/) WDB [API](https://data.gov.ie/dataset/met-eireann-weather-forecast-api/resource/5d156b15-38b8-4de9-921b-0ffc8704c88e) outputs a detailed point forecast in XML format for a coordinate point as defined by the user.
- [Calendarific](https://calendarific.com/) Global Holidays [API](https://calendarific.com/api-documentation) is a RESTful API giving you access to public, local & bank holidays and observances. An API key is required for every request to the Holiday API.

The Data Pipeline was built on AWS Services, as demonstrated in the diagram below:

![Data Pipeline]({{ site.baseurl }}/images/data-pipeline.png)
