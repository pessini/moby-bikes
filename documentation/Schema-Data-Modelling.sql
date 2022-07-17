-- Link to schema: https://app.quickdatabasediagrams.com/#/d/fWEwXP
-- DB schema diagram for Moby Bikes - MySQL

DROP TABLE IF EXISTS mobybikes.`Rental`;
DROP TABLE IF EXISTS mobybikes.`Coordinates`;
DROP TABLE IF EXISTS mobybikes.`Weather`;
DROP TABLE IF EXISTS mobybikes.`Day_Info`;
DROP TABLE IF EXISTS mobybikes.`tmpRentals`;

CREATE TABLE mobybikes.`Rental` (
    `Date` datetime  NOT NULL ,
    -- Unique bike ID used for rent bike
    `BikeID` int  NOT NULL ,
    -- Battery status when rental started
    `BatteryStart` DECIMAL(5,2)  default null ,
    -- Battery status when rental finished
    `BatteryEnd` DECIMAL(5,2)  default null ,
    -- Rental Duration = LastGPSTime - LastRentalStart
    `Duration` int  NOT NULL ,
    PRIMARY KEY (
        `Date`,`BikeID`
    )
);

-- Rentals coordinates
CREATE TABLE mobybikes.`Coordinates` (
    `Date` datetime  NOT NULL ,
    -- Unique bike ID used for rent bike
    `BikeID` int  NOT NULL ,
    -- Bike coordinates if bike is locked out of station
    `Latitude` decimal(11,7)  NULL ,
    -- Bike coordinates if bike is locked out of station
    `Longitude` decimal(11,7)  NULL ,
    PRIMARY KEY (
        `Date`,`BikeID`
    )
);

CREATE TABLE mobybikes.`Weather` (
    `Date` datetime  NOT NULL ,
    `Hour` int  NOT NULL ,
    -- Morning (from 7am to noon)
    -- Afternoon (from midday to 6pm)
    -- Evening (from 6pm to 10pm)
    -- Night (from 10pm to 5am)
    `TimeOfDay` ENUM("Morning","Afternoon","Evening","Night")  NOT NULL ,
    -- in Celsius
    `Temperature` double  NOT NULL ,
    -- in Knots (kt)
    `WindSpeed` double  NOT NULL ,
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
CREATE TABLE mobybikes.`tmpRentals` (
    -- Last time bike was rented
    `LastRentalStart` datetime  NOT NULL ,
    -- Use for rent bike
    `BikeID` int  NOT NULL ,
    -- Bike max distance in km
    `Battery` DECIMAL(5,2)  default null ,
    -- Last time bike connected with GPS
    `LastGPSTime` datetime  NOT NULL ,
    -- Bike coordinates if bike is locked out of station
    `Latitude` decimal(11,7)  NULL ,
    -- Bike coordinates if bike is locked out of station
    `Longitude` decimal(11,7)  NULL 
);

ALTER TABLE mobybikes.`Rental` ADD CONSTRAINT `fk_Rental_Date_BikeID` FOREIGN KEY(`Date`, `BikeID`)
REFERENCES mobybikes.`Coordinates`(`Date`, `BikeID`);
