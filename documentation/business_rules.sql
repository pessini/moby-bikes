DROP FUNCTION IF EXISTS RENTAL_DURATION;
DROP PROCEDURE IF EXISTS SP_GET_COORDINATES;
DROP PROCEDURE IF EXISTS check_table_exists;

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
END; //

CREATE TEMPORARY TABLE IF NOT EXISTS completed_rentals
SELECT 
	r.LastRentalStart,
	r.BikeID
FROM
(
	SELECT 
		LastRentalStart,
		BikeID,
		RANK() OVER (PARTITION BY BikeID ORDER BY LastRentalStart DESC) rent_rank
	FROM
		mobybikes.tmpRentals
	GROUP BY
		LastRentalStart, BikeID
) r 
WHERE rent_rank > 1;

DELIMITER //
CREATE PROCEDURE SP_GET_COORDINATES()
BEGIN

	SELECT
		LastRentalStart,
		BikeID,
        RENTAL_DURATION(MAX(LastGPSTime), LastRentalStart) AS duration
	FROM
		mobybikes.tmpRentals
	GROUP BY 
		LastRentalStart, BikeID
	HAVING
		(LastRentalStart,BikeID) IN (SELECT LastRentalStart,BikeID FROM completed_rentals)
	ORDER BY
		BikeID,LastRentalStart ASC;
        
END; //


DELIMITER //
CREATE PROCEDURE check_table_exists(table_name VARCHAR(100)) 
BEGIN
    DECLARE CONTINUE HANDLER FOR SQLSTATE '42S02' SET @err = 1;
    SET @err = 0;
    SET @table_name = table_name;
    SET @sql_query = CONCAT('SELECT 1 FROM ',@table_name);
    PREPARE stmt1 FROM @sql_query;
    IF (@err = 1) THEN
        SET @table_exists = 0;
    ELSE
        SET @table_exists = 1;
        DEALLOCATE PREPARE stmt1;
    END IF;
END //
DELIMITER ;

-- CALL check_table_exists('completed_rentals');
-- SELECT @table_exists;

CALL SP_GET_COORDINATES();

