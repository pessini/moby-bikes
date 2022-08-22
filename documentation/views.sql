WITH CTE_LASTMONTH_DURATION AS
(
	SELECT AVG(Duration) AS average_duration
	FROM mobybikes.Rentals
	WHERE DATE(`Date`) BETWEEN DATE_SUB( CURDATE() , INTERVAL 30 DAY) AND CURDATE()
)
SELECT average_duration FROM CTE_LASTMONTH_DURATION;

WITH CTE_LASTMONTH_RENTALS AS
	(
		SELECT COUNT(*) AS total_rentals
		FROM mobybikes.Rentals
		WHERE DATE(`Date`) BETWEEN DATE_SUB( CURDATE() , INTERVAL 30 DAY) AND CURDATE()
	)
SELECT total_rentals FROM CTE_LASTMONTH_RENTALS;

-- DATE_FORMAT(`Date`, '%Y-%m') AS yearMonth,

WITH CTE_HOURLY_TOTAL_RENTALS AS
	(
		SELECT 
			DATE_FORMAT(`Date`, '%Y-%m-%d %H:00:00') AS date_rental,
			COUNT(*) AS total_rentals
		FROM mobybikes.Rentals
		GROUP BY date_rental
		HAVING
			DATE(date_rental) BETWEEN DATE_SUB( CURDATE() , INTERVAL 3 MONTH) AND CURDATE()
	)
SELECT 
	date_rental,
	FN_TIMESOFDAY(date_rental) AS timeofday, 
	DAYNAME(date_rental) AS day_of_week, 
	total_rentals 
FROM 
	CTE_HOURLY_TOTAL_RENTALS;





