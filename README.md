<h1 align="center" style="padding: 50px">
    <p align="center">
        <img src="https://www.mobybikes.com/wp-content/uploads/2020/05/logo-1.png" width="224px"/>
    </p>
</h1>
<h3 align="center"> eBike Operations Optimization <br /><br />
Analytical Dashboard & Demand Forecasting </h3>  
<p align="center"><img src="https://img.shields.io/badge/LICENSE-MIT-blue?style=?style=flat-square&logo=appveyor&logo=none" alt="license" /></p>
<p align="center">
    <strong>
        <a href="https://mobybikes.streamlitapp.com/" target="_blank">Web App</a>
        •
        <!-- <a href="https://whimsical.com/design-docs-moby-bikes-operations-optimization-3RJyNyq2NHe8rPGzGZjrje" target="_blank">Documentation</a> -->
        <a href="https://www.pessini.me/moby-bikes/" target="_blank">Documentation</a>
    </strong>
</p>

<p align="center">
    <img src="https://i.ytimg.com/vi/-s8er6tHD3o/maxresdefault.jpg" width="550">
</p>

Moby bikes is an e-bike bike-share scheme in operation in Dublin.
Electric powered bicycles may be rented from and returned to designated cycle stands inside the designated area.

As part of Moby Operations, there is a role called "_eBike Operators_" which among its responsibilities are distributing and relocating
eBikes throughout the city, while performing safety checks and basic maintenance.

**To optimize operations, we want to predict the demand for the next hours based on weather data in order to decide whether to increase
fleet or is safe to perform safety checks and maintenance or to collect bikes for repairing.**

### In a nutshell (TL:DR)

- **Data Pipeline** - Pulls data from APIs and dumps it into an AWS S3 bucket. Reads files from S3 and stores them in a MYSQL database.

- **Minimum Viable Product (MVP)** - A web app displaying a few business metrics and charts.

- Uses **machine learning algorithms** to predict the demand for the next hours based on weather data.

- Moby Operations team will use **Dashboard** and **Rental Demand Forecasting** to make decisions and planning its daily operations.

---

[Read full documentation](https://www.pessini.me/moby-bikes/)
