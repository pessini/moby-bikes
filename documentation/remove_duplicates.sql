SET SQL_SAFE_UPDATES = 0;
DELETE FROM mobybikes.rawRentals 
WHERE 
	_id IN (
	SELECT 
		_id 
	FROM (
		SELECT 
			_id,
			ROW_NUMBER() OVER (
				PARTITION BY `LastRentalStart`,`BikeID`, `LastGPSTime`) AS row_num
		FROM 
			mobybikes.rawRentals
		
	) t
    WHERE row_num > 1
);

DELETE FROM mobybikes.Rentals_Coordinates 
WHERE 
	_id IN (
	SELECT 
		_id 
	FROM (
		SELECT 
			_id,
			ROW_NUMBER() OVER (
				PARTITION BY `Date`,`BikeID`, `Latitude`, `Longitude`) AS row_num
		FROM 
			mobybikes.Rentals_Coordinates
		
	) t
    WHERE row_num > 1
);

SET SQL_SAFE_UPDATES = 1;
