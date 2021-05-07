

# Avian influenza or "Bird Flu" is a contagious and often fatal viral disease of birds. 
# Wild birds, particularly wild migratory water birds are considered to be the main reservoir 
# of avian influenza viruses. There is a constant risk of avian influenza being introduced into 
# Ireland from wild birds particularly from November onwards each year as this is when migratory 
# birds arrive and congregate on wetlands, mixing with resident species. The attached file is a 
# data set of the locations of bird species captured in Ireland from 1980 to 2020 and wild birds 
# that are targeted for the H5N1 strain of avian flu.

# https://data.gov.ie/dataset/h5n1-wild-bird-species-identification

library(psych)

df <- read.csv(file = 'bird-flu.csv')

head(df)
View(df)

df$target_H5_HPAI <- as.factor(df$target_H5_HPAI)

summary(df$target_H5_HPAI)

describeBy(df$target_H5_HPAI)

bike <- read.csv(file = "bleeperbike-historical-data-072020.csv")
head(bike)
str(bike)


bike$vehicle_type <- as.factor(bike$vehicle_type)
summary(bike$vehicle_type)


weather <- read.csv(file = "dly2275.csv")
head(weather)  
str(weather)

##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################
##############################################################################################################


library(dplyr)
library(lubridate)
moby_bikes <- read.csv(file = "moby-bikes-historical-data-032021.csv")

moby_bikes1 <- read.csv(file = "moby-bikes-historical-data-102020.csv")
moby_bikes1$BikeTypeName <- as.factor(moby_bikes1$BikeTypeName)
moby_bikes1$BikeID <- as.factor(moby_bikes1$BikeID)

bikes_5 <- moby_bikes1 %>% 
            filter(BikeID == "5") %>% 
            select(HarvestTime, BikeID, Battery, LastGPSTime, LastRentalStart) %>%
            mutate(across(HarvestTime, ymd_hms)) %>%
            mutate(across(LastGPSTime, ymd_hms)) %>%
            mutate(across(LastRentalStart, ymd_hms)) %>%
            arrange(HarvestTime)

new_df <- bikes_5 %>% mutate(Diff_Min = round(as.numeric(difftime(LastGPSTime, LastRentalStart, units = c("mins"))),0) )


head(new_df, n=30)
View(bikes_5)


str(moby_bikes1$BikeTypeName)
summary(moby_bikes1$BikeTypeName)

summary(moby_bikes1$Battery)
