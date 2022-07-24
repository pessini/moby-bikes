-- --------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS RENTAL_DURATION;
DROP PROCEDURE IF EXISTS SP_COORDINATES;
DROP PROCEDURE IF EXISTS SP_NEW_RENTALS;
DROP PROCEDURE IF EXISTS SP_COMPLETED_RENTALS_TO_PROCESS;
DROP PROCEDURE IF EXISTS SP_CLEASING_PROCESSED_RENTALS;
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
    RETURN TIMESTAMPDIFF(MINUTE, LAST_GPSTIME, RENTAL_START) * -1;
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE SP_COMPLETED_RENTALS_TO_PROCESS()
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
		(LastRentalStart,BikeID) IN (SELECT LastRentalStart,BikeID FROM mobybikes.TEMP_completed_rentals);
	
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE SP_NEW_RENTALS()
BEGIN

	CALL SP_COMPLETED_RENTALS_TO_PROCESS();

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
        FLOOR (CAST( GROUP_CONCAT( IF ( RentStarting = 0, RENTAL_DURATION(LastGPSTime,LastRentalStart), NULL )) AS DECIMAL(12,1))) AS duration
    FROM 
		CTE_RENTAL_START_FINISH
	GROUP BY
		LastRentalStart, BikeID
	ORDER BY
		BikeID, LastRentalStart ASC;
        
	CALL SP_COORDINATES();
    CALL SP_CLEASING_PROCESSED_RENTALS();
        
END //
DELIMITER ;