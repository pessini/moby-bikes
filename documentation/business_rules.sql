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

	INSERT INTO mobybikes.Rentals_Coordinates (Date, BikeID, Latitude, Longitude)
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

	INSERT INTO mobybikes.Rentals (Date, BikeID, BatteryStart, BatteryEnd, Duration)
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
    
	INSERT INTO mobybikes.Log_Weather (`Date`, `Processed`, `Errors`)
    VALUES (STR_TO_DATE(DATE_FILE,'%Y-%m-%d'), weather_events, number_errors);
	
END //
DELIMITER ;
