-- --------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS RENTAL_DURATION;
DROP PROCEDURE IF EXISTS SP_COORDINATES;
DROP PROCEDURE IF EXISTS SP_NEW_RENTALS;
DROP PROCEDURE IF EXISTS SP_COMPLETED_RENTALS_TO_PROCESS;
DROP PROCEDURE IF EXISTS SP_CLEASING_PROCESSED_RENTALS;
DROP PROCEDURE IF EXISTS SP_LOG_RENTAL_EVENTS;
DROP PROCEDURE IF EXISTS SP_GET_NUMBER_OPENED_RENTALS;
DROP TABLE IF EXISTS TEMP_completed_rentals;
-- DROP TEMPORARY TABLE IF EXISTS completed_rentals;

-- --------------------------------------------------------------------------------------------------
-- Function to calculate rentals duration
/** 
	Assumption: Due to lack of information and data, to calculate the duration rental time I am assuming that when a new 
    bike rental starts the duration in *minutes* will be calculated by: RentalDuration = LastGPSTime - LastRentalStart
*/
-- --------------------------------------------------------------------------------------------------
DELIMITER //
CREATE FUNCTION RENTAL_DURATION(LAST_GPSTIME DATETIME, RENTAL_START DATETIME) 
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


DELIMITER //
CREATE PROCEDURE SP_LOG_RENTAL_EVENTS(
	IN rentals_to_process INT,
    IN rentals_processed INT,
    IN number_errors INT
)
BEGIN

	INSERT INTO mobybikes.Log_events (`Date`, `Rentals_ToProcess`, `Rentals_Processed`, `Errors`)
    VALUES (NOW(), rentals_to_process, rentals_processed, number_errors);
	
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE SP_GET_NUMBER_RENTALS(
	IN rental_status VARCHAR(50),
	OUT number_rentals INT)
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
    )
    IF rental_status = "OPENED" THEN
		SELECT COUNT(*) INTO number_rentals FROM CTE_OPENED_RENTALS WHERE rent_rank = 1;
	ELSEIF rental_status = "COMPLETED" THEN
		SELECT COUNT(*) INTO number_rentals FROM CTE_OPENED_RENTALS WHERE rent_rank > 1;
	ELSEIF rental_status = "TOTAL" THEN
		SELECT COUNT(*) INTO number_rentals FROM CTE_OPENED_RENTALS;
    END IF;
    -- rent_rank = 1 - Opened Rentals
    -- rent_rank > 1 - Completed Rentals
	
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE SP_COMPLETED_RENTALS_TO_PROCESS(OUT rentals_to_process INT)
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

DELIMITER //
CREATE PROCEDURE SP_CLEASING_PROCESSED_RENTALS()
BEGIN
	SET SQL_SAFE_UPDATES = 0;
	DELETE FROM mobybikes.rawRentals WHERE (LastRentalStart,BikeID) IN (SELECT LastRentalStart,BikeID FROM mobybikes.TEMP_completed_rentals);
    DROP TABLE IF EXISTS TEMP_completed_rentals;
    SET SQL_SAFE_UPDATES = 1;
	
END //
DELIMITER ;

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

DELIMITER //
CREATE PROCEDURE SP_NEW_RENTALS()
BEGIN

	DECLARE rentals_to_process, rentals_processed, number_errors INT;
    DECLARE total_completed_rentals, total_opened_rentals INT;

	CALL SP_COMPLETED_RENTALS_TO_PROCESS(rentals_to_process);

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
        FLOOR (CAST( GROUP_CONCAT( RENTAL_DURATION(LastGPSTime,LastRentalStart) ORDER BY RentStarting ASC ) AS DECIMAL(12,1))) AS duration
    FROM 
		CTE_RENTAL_START_FINISH
	GROUP BY
		LastRentalStart, BikeID
	ORDER BY
		BikeID, LastRentalStart ASC;
        
	CALL SP_COORDINATES();
    
    -- count(*) rawRentals
    SET total_completed_rentals := (SELECT COUNT(*) FROM mobybikes.TEMP_completed_rentals);
    
    CALL SP_CLEASING_PROCESSED_RENTALS();
    
	CALL SP_GET_NUMBER_OPENED_RENTALS(total_opened_rentals);

    SET rentals_processed := total_completed_rentals - total_opened_rentals;
    
    SET number_errors := rentals_to_process - rentals_processed;
    
    CALL SP_LOG_RENTAL_EVENTS(rentals_to_process, rentals_processed, number_errors);
        
END //
DELIMITER ;