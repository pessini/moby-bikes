/** 
Assumption: Due to lack of information and data, to calculate the duration rental time I am assuming that when a new bike rental starts 
	the duration in *minutes* will be calculated by: RentalDuration = LastGPSTime - LastRentalStart
*/
DROP FUNCTION IF EXISTS rental_duration;
DROP PROCEDURE IF EXISTS check_rentals;

DELIMITER //
CREATE FUNCTION rental_duration(last_gpstime datetime, rental_start datetime) 
RETURNS int
deterministic
BEGIN
    RETURN TIMESTAMPDIFF(MINUTE, last_gpstime, rental_start) * -1;
END; //

/** 
https://www.geeksforgeeks.org/different-types-of-procedures-in-mysql/
https://www.tutorialspoint.com/How-MySQL-IF-ELSE-statement-can-be-used-in-a-stored-procedure
*/
delimiter //
create procedure check_rentals()
begin 
	-- declare bikes int;
--     declare rentals_dt datetime;
	select 
		LastRentalStart,
		BikeID,
        rental_duration(MAX(LastGPSTime),LastRentalStart) as duration
        
    from mobybikes.tmpRentals
    group by
		LastRentalStart, BikeID
    order by LastRentalStart asc;
    
    -- insert into 
end //



call check_rentals(); //