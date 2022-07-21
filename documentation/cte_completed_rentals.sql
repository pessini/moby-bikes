WITH CTE_COMPLETED_RENTALS as
(
	select 
		r.LastRentalStart,
		r.BikeID
	from
	(
		select 
			LastRentalStart,
			BikeID,
			RANK() OVER (PARTITION BY BikeID ORDER BY LastRentalStart DESC) rent_rank
		from
			mobybikes.tmpRentals
		group by 
			LastRentalStart, BikeID
		
	) r WHERE rent_rank > 1
)

SELECT * FROM CTE_COMPLETED_RENTALS


-- SELECT
-- 	LastRentalStart,
--     BikeID,
--     LastGPSTime
-- FROM
-- 	cte_lastRows
-- where
-- 	(LastRentalStart,BikeID) not in (
-- 							select max(LastRentalStart),BikeID from cte_lastRows group by LastRentalStart, BikeID
--                             )
-- order by
-- 	LastRentalStart ASC;