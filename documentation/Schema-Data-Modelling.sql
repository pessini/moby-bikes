-- Link to schema: 
-- https://app.quickdatabasediagrams.com/#/d/fWEwXP
-- DB schema diagram for Moby Bikes - MySQL

CREATE DATABASE IF NOT EXISTS mobybikes;

-- ALTER TABLE mobybikes.Rentals_Coordinates DROP CONSTRAINT fk_Rental_Date_BikeID;

DROP TABLE IF EXISTS mobybikes.`Rentals`;
DROP TABLE IF EXISTS mobybikes.`Rentals_Coordinates`;
DROP TABLE IF EXISTS mobybikes.`Weather`;
DROP TABLE IF EXISTS mobybikes.`Day_Info`;
DROP TABLE IF EXISTS mobybikes.`rawRentals`;
DROP TABLE IF EXISTS mobybikes.`Log_Rentals`;
DROP TABLE IF EXISTS mobybikes.`Log_Weather`;

CREATE TABLE mobybikes.`Rentals` (
	`_id` INT AUTO_INCREMENT PRIMARY KEY,
    `Date` datetime  NOT NULL ,
    -- Unique bike ID used for rent bike
    `BikeID` int  NOT NULL ,
    -- Battery status when rental started
    `BatteryStart` int signed  default null ,
    -- Battery status when rental finished
    `BatteryEnd` int signed  default null ,
    -- Rental Duration = LastGPSTime - LastRentalStart
    `Duration` BIGINT NULL ,
    CONSTRAINT rental UNIQUE (`Date`,`BikeID`)
);

-- Rentals coordinates
CREATE TABLE mobybikes.`Rentals_Coordinates` (
	`_id` INT AUTO_INCREMENT PRIMARY KEY,
    `Date` datetime  NOT NULL ,
    -- Unique bike ID used for rent bike
    `BikeID` int  NOT NULL ,
    -- Bike coordinates if bike is locked out of station
    `Latitude` decimal(11,7)  NULL ,
    -- Bike coordinates if bike is locked out of station
    `Longitude` decimal(11,7)  NULL
);

CREATE TABLE mobybikes.`Weather` (
	`_id` INT AUTO_INCREMENT PRIMARY KEY,
    `Date` date  NOT NULL ,
    `Hour` int  NOT NULL ,
    -- Morning (from 7am to noon)
    -- Afternoon (from midday to 6pm)
    -- Evening (from 6pm to 10pm)
    -- Night (from 10pm to 5am)
    `TimeOfDay` ENUM("Morning","Afternoon","Evening","Night")  NOT NULL ,
    -- in Celsius
    `Temperature` double  NOT NULL ,
    -- in Knots (kt)
    `WindSpeed` INT  NOT NULL ,
    -- Relative humidity (%)
    `Humidity` int  NOT NULL ,
    -- in millimetres (mm)
    `Rain` double  NOT NULL ,
    -- no rain = 0
    -- drizzle - 0.1~0.3
    -- light rain - 0.3~0.5
    -- moderate rain -  0.5~4
    -- heavy rain - >4
    `RainLevel` ENUM("no rain","drizzle","light rain","moderate rain","heavy rain")  NOT NULL 
);

-- Date and time features
CREATE TABLE mobybikes.`Day_Info` (
	`_id` INT AUTO_INCREMENT PRIMARY KEY,
    `Date` date  NOT NULL ,
    -- Monday = 0 ~ Sunday = 6
    `DayofWeek` tinyint UNSIGNED NOT NULL ,
    -- Irish National Bank Holidays
    `Holiday` boolean  NOT NULL ,
    -- Monday to Friday AND not Bank Holiday
    `WorkingDay` boolean  NOT NULL ,
    -- Spring | Summer | Autumn | Winter
    `Season` ENUM("Spring","Summer","Autumn","Winter")  NOT NULL 
);

-- Table with all rentals before preprocess
CREATE TABLE mobybikes.`rawRentals` (
	`_id` INT AUTO_INCREMENT PRIMARY KEY,
    -- Last time bike was rented
    `LastRentalStart` datetime  NOT NULL ,
    -- Use for rent bike
    `BikeID` int  NOT NULL ,
    -- Bike max distance in km
    `Battery` int signed  default null ,
    -- Last time bike connected with GPS
    `LastGPSTime` datetime  NOT NULL ,
    -- Bike coordinates if bike is locked out of station
    `Latitude` decimal(11,7)  NULL ,
    -- Bike coordinates if bike is locked out of station
    `Longitude` decimal(11,7)  NULL,
    CONSTRAINT gps_rental UNIQUE(`LastRentalStart`,`BikeID`, `LastGPSTime`)
);

-- Log events to track processing errors on Rentals
CREATE TABLE mobybikes.`Log_Rentals` (
	`_id` INT AUTO_INCREMENT PRIMARY KEY,
    `Date` DATETIME NOT NULL ,
    -- Total Rentals processed
    `Processed` int NULL ,
    -- Number of Rentals failed to be processed
    `Errors` int NULL
);

-- Log events to track processing errors on Weather Data
CREATE TABLE mobybikes.`Log_Weather` (
	`_id` INT AUTO_INCREMENT PRIMARY KEY,
    `Date` DATE NOT NULL ,
    -- Weather data processed
    `Processed` int NULL ,
    -- Number of hourly weather data failed to be processed
    `Errors` int NULL
);

ALTER TABLE mobybikes.`Rentals_Coordinates` ADD CONSTRAINT `fk_Rental_Date_BikeID` FOREIGN KEY(`Date`, `BikeID`)
REFERENCES mobybikes.`Rentals`(`Date`, `BikeID`);

