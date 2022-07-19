SET GLOBAL local_infile = true;
-- truncate mobybikes.tmpRentals;

LOAD DATA LOCAL INFILE '/Users/pessini/Dropbox/Data-Science/moby-bikes/documentation/fev_sqltest.csv'  INTO TABLE `mobybikes`.`tmpRentals` CHARACTER SET UTF8MB4
FIELDS TERMINATED BY ',' ENCLOSED BY '' LINES TERMINATED BY '\n' IGNORE 1 LINES;

-- LOAD DATA LOCAL INFILE '/Users/lpessini/TUDublin/moby-bikes/documentation/fev_sqltest.csv'  INTO TABLE `mobybikes`.`tmpRentals` CHARACTER SET UTF8MB4
-- FIELDS TERMINATED BY ',' ENCLOSED BY '' LINES TERMINATED BY '\n' IGNORE 1 LINES;
SET GLOBAL local_infile = false;
