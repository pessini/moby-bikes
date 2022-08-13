SET GLOBAL local_infile = true;
-- TRUNCATE mobybikes.rawRentals;

LOAD DATA LOCAL INFILE '/Users/pessini/Dropbox/Data-Science/moby-bikes/data/raw/mysql-data/12082022.csv'  INTO TABLE `mobybikes`.`rawRentals` CHARACTER SET UTF8MB4
FIELDS TERMINATED BY ',' ENCLOSED BY '' LINES TERMINATED BY '\n' IGNORE 1 LINES;

-- LOAD DATA LOCAL INFILE '/Users/lpessini/TUDublin/moby-bikes/data/raw/mysql-data/042021.csv'  INTO TABLE `mobybikes`.`rawRentals` CHARACTER SET UTF8MB4
-- FIELDS TERMINATED BY ',' ENCLOSED BY '' LINES TERMINATED BY '\n' IGNORE 1 LINES;

SET GLOBAL local_infile = false;

CALL SP_RENTALS_PROCESSING();