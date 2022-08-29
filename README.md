<p align="center"> 
  <img src="https://www.mobybikes.com/wp-content/uploads/2020/05/logo-1.png" width="224px"/>
</p>
<h1 align="center"> eBike Operations Optimization </h1>
<h3 align="center"> Analytical Dashboard & Rental Demand Prediction </h3>  
<p align="center"><a href="https://github.com/create-go-app/cli/releases" target="_blank"><img src="https://img.shields.io/badge/python-v3.9.6-blue?style=for-the-badge&logo=Python" alt="cli version" /></a> <img src="https://img.shields.io/badge/ML_Accuracy-89.2%25-success?style=for-the-badge&logo=none" alt="go cover" /> <img src="https://img.shields.io/badge/license-mit-red?style=for-the-badge&logo=none" alt="license" /></p>
<p align="center">
    <strong>
        <a href="https://pessini-moby-bikes-dashboardapp-hhvohw.streamlitapp.com/" target="_blank">Live Demo</a>
        •
        <a href="https://whimsical.com/design-docs-moby-bikes-operations-optimization-3RJyNyq2NHe8rPGzGZjrje" target="_blank">Documentation</a>
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
fleet or is safe to perform safety checks and maintenance and even to collect bikes for repair.**

### In a nutshell (TL:DR)

- **Data Pipeline** - Pull data from APIs and dump it into a AWS S3 bucket. Read files from S3 and store them in a MYSQL database.

- **Minimum Viable Product (MVP)** - Creates a web app that shows a few business metrics and a few charts.

- Uses **machine learning algorithms** to predict the demand for the next hours based on weather data.

- Moby Operations team will use **Dashboard** and **Rental Demand Forecasting** to make decisions and planning its daily operations.

---

Read full documentation [here](https://whimsical.com/design-docs-moby-bikes-operations-optimization-3RJyNyq2NHe8rPGzGZjrje)