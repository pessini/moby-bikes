-- --------------------------------------------------------------------------------------------------
-- CTE to query all rentals (rental start and bikeid) but the last one which could be "in progress"
-- All selected rentals will be used to process later
-- --------------------------------------------------------------------------------------------------
WITH CTE_COMPLETED_RENTALS AS
(
	SELECT 
		r.LastRentalStart,
		r.BikeID
		-- ,r.rent_rank
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
	WHERE rent_rank > 1
)