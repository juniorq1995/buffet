# buffet
 portolio tool
# Go through list of exchanges
# All US exchanges are combined into one virtual exchange ‘US,’ which includes NYSE, NASDAQ, ARCA, and OTC/PINK tickers.
# All indices and commodities are in virtual exchanges INDX and COMM, respectively.
# Need opening/closing times for each exchange as well as which ones are past the date line (Goes off of the UTC date for GB)
# Create a list of symbols for each exchanges
https://eodhistoricaldata.com/api/exchanges/US?api_token={YOUR_API_KEY}&fmt=json
# periodically call to get new supported companies

# iterate through each exchange and the symbols registered
https://eodhistoricaldata.com/api/eod/AAPL.US?api_token={YOUR_API_KEY}&period=d.
https://eodhistoricaldata.com/knowledgebase/api-for-historical-data-and-volumes/

#
Save EOD data in table, 1 for each symbol

# Find total return from each symbol for past 1,2,3,4,8,12,16,20 years
# And save in different table
# Later calculate avg return, variance, and STD
# Has lag of one day since it uses EOD data
# Ranks symbols for each exchange as well as overall

# Compare to separate ranking of supported indices
https://eodhistoricaldata.com/knowledgebase/list-supported-indices/

# Later target periods in history that experienced strong recessions or wars to highlight companies that performed well and some that didnt

# 2 schemas, one for saving EOD data and another for saving metadata (i.e. rankings, ROI, etc.)

# Will need to run after each exchange closes and update the rankings after a GMT time has passed (considering the time and date differences)
# Have settings that control how often the data is updated
# Default will be weekly on Sunday with the rankings being updated as well
# db will also be updated daily using api calls
# usage of api limits will be measured on both ends as well as the time spent

# run 'pgsql' to start postgres in terminal