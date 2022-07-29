INSERT INTO mobybikes.Log_Files(`Date`, `Rentals_Filename`, `Weather_Filename`)
VALUES (NOW(), "rental.json", "weather.xml");

-- CALL SP_RENTALS_PROCESSING(LAST_INSERT_ID());

CALL SP_LOG_WEATHER_EVENTS(LAST_INSERT_ID());
