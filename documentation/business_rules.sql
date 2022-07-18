/** 
Assumption: Due to lack of information and data, to calculate the duration rental time I am assuming that when a new bike rental starts 
	the duration in *minutes* will be calculated by: RentalDuration = LastGPSTime - LastRentalStart
    TIMESTAMPDIFF(unit,datetime_expr1,datetime_expr2)
*/
-- DROP FUNCTION IF EXISTS rental_duration;
-- DELIMITER //
-- CREATE FUNCTION rental_duration(last_gpstime datetime, rental_start datetime) 
-- RETURNS int
-- BEGIN
--     RETURN TIMESTAMPDIFF(MINUTE, last_gpstime, rental_start) * -1;
-- END; //

/** 
https://www.geeksforgeeks.org/different-types-of-procedures-in-mysql/
https://www.tutorialspoint.com/How-MySQL-IF-ELSE-statement-can-be-used-in-a-stored-procedure
*/
DROP PROCEDURE IF EXISTS check_rentals;
delimiter //
create procedure check_rentals() 
begin 
	select 
		LastRentalStart, BikeID
    from mobybikes.tmpRentals
    group by LastRentalStart, BikeID
    order by BikeID,LastRentalStart asc; 
end //

call check_rentals(); //