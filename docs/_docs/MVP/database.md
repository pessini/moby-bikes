---
title: Database Modeling
category: Minimum Viable Product (MVP)
order: 2
---

An AWS Aurora MySQL database will be used to store the data after being dumped on AWS S3 Bucket. An [entity-relationship (ER) diagram](https://www.quickdatabasediagrams.com/) was used as initial schema:

| ![Database Model]({{ site.baseurl }}/images/DBDataModel.png) |
| :--: |
| *Entity-Relationship (ER) Diagram* |

See online: [https://app.quickdatabasediagrams.com/#/d/fWEwXP](https://app.quickdatabasediagrams.com/#/d/fWEwXP)

## Business Rules - MySQL

A set of functions and stored procedures were created to handle processing and logging with SQL.

```sql
-- --------------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS mobybikes.TEMP_completed_rentals;
-- DROP TEMPORARY TABLE IF EXISTS completed_rentals;

-- --------------------------------------------------------------------------------------------------
-- Function to calculate rentals duration
/**
	Assumption: Due to lack of information and data, to calculate the duration rental time I am assuming that when a new
    bike rental starts the duration in *minutes* will be calculated by: RentalDuration = LastGPSTime - LastRentalStart
*/
-- --------------------------------------------------------------------------------------------------
USE mobybikes;

DROP FUNCTION IF EXISTS FN_RENTAL_DURATION;
DELIMITER //
CREATE FUNCTION FN_RENTAL_DURATION(LAST_GPSTIME DATETIME, RENTAL_START DATETIME)
RETURNS INT
DETERMINISTIC
BEGIN
	DECLARE duration BIGINT DEFAULT 0;

    SET duration = TIMESTAMPDIFF(MINUTE, RENTAL_START, LAST_GPSTIME);

    IF duration < 0 THEN
		SET duration = 0;
	END IF;

    RETURN duration;
END //
DELIMITER ;

DROP FUNCTION IF EXISTS FN_TIMESOFDAY;
DELIMITER //
CREATE FUNCTION FN_TIMESOFDAY(rental_date DATETIME)
RETURNS VARCHAR(10)
DETERMINISTIC
BEGIN
	DECLARE timeofday VARCHAR(10);
  DECLARE rental_hour INT;

  SET rental_hour := HOUR(rental_date);

  IF rental_hour < 7 THEN
		SET timeofday := 'Night';
	ELSEIF rental_hour >= 7 AND rental_hour < 12 THEN
		SET timeofday := 'Morning';
	ELSEIF rental_hour >= 12 AND rental_hour < 18 THEN
		SET timeofday := 'Afternoon';
	ELSEIF rental_hour >= 18 AND rental_hour < 23 THEN
		SET timeofday := 'Evening';
	ELSE
		SET timeofday := 'Night';
	 END IF;

  RETURN timeofday;
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS SP_LOG_RENTAL_EVENTS;
DELIMITER //
CREATE PROCEDURE SP_LOG_RENTAL_EVENTS(
    IN rentals_processed INT,
    IN number_errors INT
)
BEGIN

	INSERT INTO mobybikes.Log_Rentals (`Date`, `Processed`, `Errors`)
    VALUES (NOW(), rentals_processed, number_errors);

END //
DELIMITER ;

DROP PROCEDURE IF EXISTS SP_GET_TOTAL_RENTALS_TO_PROCESS;
DELIMITER //
CREATE PROCEDURE SP_GET_TOTAL_RENTALS_TO_PROCESS(OUT total_rentals INT)
BEGIN

	SELECT
		COUNT(*) INTO total_rentals
	FROM
    (
		SELECT
			LastRentalStart,
			BikeID
		FROM
			mobybikes.rawRentals
		GROUP BY
			LastRentalStart, BikeID
	) AS r;

END //
DELIMITER ;

DROP PROCEDURE IF EXISTS SP_GET_TOTAL_OPENED_RENTALS;
DELIMITER //
CREATE PROCEDURE SP_GET_TOTAL_OPENED_RENTALS(OUT opened_rentals INT)
BEGIN
    WITH CTE_OPENED_RENTALS AS (
		SELECT
			r.LastRentalStart,
			r.BikeID,
			r.rent_rank
		FROM
		(
			SELECT
				LastRentalStart,
				BikeID,
				RANK() OVER (PARTITION BY BikeID ORDER BY LastRentalStart DESC) rent_rank
			FROM
				mobybikes.rawRentals
			GROUP BY
				LastRentalStart, BikeID
		) r
        WHERE rent_rank = 1
    )
    -- returning the number of rentals NOT completed
	SELECT COUNT(*) INTO opened_rentals FROM CTE_OPENED_RENTALS;

END //
DELIMITER ;

DROP PROCEDURE IF EXISTS SP_COMPLETED_RENTALS;
DELIMITER //
CREATE PROCEDURE SP_COMPLETED_RENTALS(OUT rentals_to_process INT)
BEGIN
	-- The ERROR 1137 is a known issue with MySQL that hasn’t got any fix since 2008.
	-- Not creating a temporary table because of an issue referenced above.

  DROP TABLE IF EXISTS TEMP_completed_rentals;

	CREATE TABLE TEMP_completed_rentals
	SELECT
		r.LastRentalStart,
		r.BikeID,
		r.rent_rank
	FROM
	(
		SELECT
			LastRentalStart,
			BikeID,
			RANK() OVER (PARTITION BY BikeID ORDER BY LastRentalStart DESC) rent_rank
		FROM
			mobybikes.rawRentals
		GROUP BY
			LastRentalStart, BikeID
	) r
	WHERE rent_rank > 1;

    -- returning the number of rentals to be processed
	SELECT COUNT(*) INTO rentals_to_process FROM TEMP_completed_rentals;

END //
DELIMITER ;

DROP PROCEDURE IF EXISTS SP_CLEASING_PROCESSED_RENTALS;
DELIMITER //
CREATE PROCEDURE SP_CLEASING_PROCESSED_RENTALS()
BEGIN
	SET SQL_SAFE_UPDATES = 0;
	DELETE FROM mobybikes.rawRentals WHERE (LastRentalStart,BikeID) IN (SELECT LastRentalStart,BikeID FROM mobybikes.TEMP_completed_rentals);
    DROP TABLE IF EXISTS TEMP_completed_rentals;
    SET SQL_SAFE_UPDATES = 1;
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS SP_COORDINATES;
DELIMITER //
CREATE PROCEDURE SP_COORDINATES()
BEGIN

	INSERT IGNORE INTO mobybikes.Rentals_Coordinates (`Date`, BikeID, Latitude, Longitude)
    SELECT
		LastRentalStart,
        BikeID,
        Latitude,
        Longitude
	FROM
		mobybikes.rawRentals
	WHERE
		(LastRentalStart,BikeID) IN (SELECT LastRentalStart,BikeID FROM mobybikes.TEMP_completed_rentals)
	AND
		(Latitude IS NOT NULL OR Longitude IS NOT NULL)
	AND
		(Latitude <> 0 OR Longitude <> 0);

END //
DELIMITER ;

DROP PROCEDURE IF EXISTS SP_RENTALS_PROCESSING;
DELIMITER //
CREATE PROCEDURE SP_RENTALS_PROCESSING()
BEGIN

  DECLARE total_completed_rentals, total_opened_rentals, rentals_to_process, number_errors INT;

	-- creates a temporary table and returns the total of completed rentals
	CALL SP_COMPLETED_RENTALS(total_completed_rentals);

	INSERT IGNORE INTO mobybikes.Rentals (Date, BikeID, BatteryStart, BatteryEnd, Duration)
	WITH CTE_RENTAL_START_FINISH AS (
		SELECT
			t.LastRentalStart,
            t.BikeID,
            t.Battery,
            t.LastGPSTime,
            CASE
				WHEN t.RN_RentalStart = 1 THEN 1
				ELSE 0
			END AS RentStarting
		FROM
			(SELECT
				LastRentalStart, BikeID, Battery, LastGPSTime,
				ROW_NUMBER() OVER(PARTITION BY LastRentalStart, BikeID ORDER BY LastGPSTime) AS RN_RentalStart,
				ROW_NUMBER() OVER(PARTITION BY LastRentalStart, BikeID ORDER BY LastGPSTime DESC) AS RN_RentalFinished
			FROM
				mobybikes.rawRentals
			WHERE
				(LastRentalStart,BikeID) IN (SELECT LastRentalStart,BikeID FROM mobybikes.TEMP_completed_rentals) -- get only finished rentals from temp table
			ORDER BY
				BikeID,LastRentalStart ASC) t
		WHERE
			t.RN_RentalStart = 1 OR t.RN_RentalFinished = 1
    )
    SELECT
		LastRentalStart,
        BikeID,
        FLOOR (CAST( GROUP_CONCAT( CASE WHEN RentStarting = 1 THEN Battery ELSE NULL END) AS DECIMAL(12,1))) AS BatteryStart,
        FLOOR (CAST( GROUP_CONCAT( CASE WHEN RentStarting = 0 THEN Battery ELSE NULL END) AS DECIMAL(12,1))) AS BatteryEnd,
        -- ORDER BY RentStarting ASC so the first row to calculate would be with RentStarting = 0 (finished rental row)
        -- Not using IF because some rows have only one and then if there is only row with RentStarting=1, it will use that one
        FLOOR (CAST( GROUP_CONCAT( FN_RENTAL_DURATION(LastGPSTime,LastRentalStart) ORDER BY RentStarting ASC ) AS DECIMAL(12,1))) AS duration
    FROM
		CTE_RENTAL_START_FINISH
	GROUP BY
		LastRentalStart, BikeID
	ORDER BY
		BikeID, LastRentalStart ASC;

	CALL SP_COORDINATES();

	-- returns the total of opened rentals (not to be processed yet)
    CALL SP_GET_TOTAL_OPENED_RENTALS(total_opened_rentals);
    CALL SP_CLEASING_PROCESSED_RENTALS();

    -- Get rentals that are left to process (it should be only opened rentals)
    CALL SP_GET_TOTAL_RENTALS_TO_PROCESS(rentals_to_process);

    -- if = 0 there is no error
    -- if > 0 there are some rentals left which weren't processed
    SET number_errors := rentals_to_process - total_opened_rentals;

    -- log the number of processed rentals and the number of errors occurred when processing them
    CALL SP_LOG_RENTAL_EVENTS(total_completed_rentals, number_errors);

END //
DELIMITER ;


-- --------------------------------------------------------------------------------------------------
-- WEATHER LOG
-- --------------------------------------------------------------------------------------------------
USE mobybikes;
DROP PROCEDURE IF EXISTS SP_LOG_WEATHER_EVENTS;
DELIMITER //
CREATE PROCEDURE SP_LOG_WEATHER_EVENTS(IN DATE_FILE CHAR(10))
BEGIN
    DECLARE weather_events, number_errors INT;

    SELECT COUNT(*) INTO weather_events FROM mobybikes.Weather WHERE DATE(`Date`) = STR_TO_DATE(DATE_FILE,'%Y-%m-%d');

	SET number_errors := 24 - weather_events; -- it should have been recorded 24 hours

	INSERT IGNORE INTO mobybikes.Log_Weather (`Date`, `Processed`, `Errors`)
    VALUES (STR_TO_DATE(DATE_FILE,'%Y-%m-%d'), weather_events, number_errors);

END //
DELIMITER ;

```

## Schema MySQL Script

SQL script for creating database schema.

```sql
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

```
