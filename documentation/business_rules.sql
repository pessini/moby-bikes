/** 
Assumption: Due to lack of information and data, to calculate the duration rental time I am assuming that when a new bike rental starts 
	the duration in *minutes* will be calculated by: RentalDuration = LastGPSTime - LastRentalStart
    TIMESTAMPDIFF(unit,datetime_expr1,datetime_expr2)
*/

-- DELIMITER //
-- CREATE FUNCTION rental_duration(last_gpstime datetime, rental_start datetime) 
-- RETURNS int
-- BEGIN
--     RETURN TIMESTAMPDIFF(MINUTE, last_gpstime, rental_start);
-- END;
-- //

/** 
Error Code: 1418. This function has none of DETERMINISTIC, NO SQL, or READS SQL DATA in its declaration 
and binary logging is enabled (you *might* want to use the less safe log_bin_trust_function_creators variable)
*/
DROP PROCEDURE IF EXISTS check_rentals;
delimiter //
create procedure check_rentals() 
begin 
	select * from mobybikes.tmpRentals order by LastRentalStart ASC; 
end //

call check_rentals(); //