# Here shall be written the code that builds my portfolio
# input data and calculate the ROI from different companies and average all the companies to represent the "market"
# look at both the open and the close
# company symbol,ROI per year starting from recent, going back 15 years at the most
# company symbol, ROI past 15 years, ROI past 10 years, ROI past 5 years
import psycopg2
import sys, os
import numpy as np
import pandas as pd
import example_psql as creds
import pandas.io.sql as psql
import requests
import time
import Constants
from datetime import date, datetime, timedelta
import json

service_key = Constants.EOD_API_TOKEN
exchanges = ['lse']
def get_nearest_day(missing_day, idx):
    while missing_day not in idx:
        missing_day = missing_day + timedelta(days=1)
    return missing_day
def get_all_exchange_symbols(exchange):
    # API return format is:
    # {"Code":"XXX", "Name": "X", "Country": "USA", "Exchange": "NASDAQ", "Currency": "USD", "Type": "Common Stock"},
    return requests.get('https://eodhistoricaldata.com/api/exchanges/US?api_token=%s&fmt=json' % service_key).text

def get_eod_for_symbol(symbol, exchange, period='d', order='d'):
    return requests.get('https://eodhistoricaldata.com/api/eod/%s.%s?api_token=%s&period=%s&order=%s&fmt=json' % (symbol, exchange, service_key, period, order)).text

def connect_to_db():
    conn_string = "host=" + creds.PGHOST + " port=" + "5432" + " dbname=" + creds.PGDATABASE + " user=" + creds.PGUSER \
                  + " password=" + creds.PGPASSWORD
    conn = psycopg2.connect(conn_string)
    print("Connected!")

def get_total_roi_for_years(years_back, df):
    latest = df.first_valid_index()
    latest_price = df[latest]
    years_back_date = latest - timedelta(days=years_back*365)
    if years_back_date < df.last_valid_index():
        return None
    if years_back_date not in df.index:
        years_back_date = get_nearest_day(years_back_date, df.index)
    years_back_price = df[years_back_date]
    return (latest_price - years_back_price) / years_back_price

def get_total_roi(df):
    latest = df.first_valid_index()
    latest_price = df[latest]
    years_back_price = df[df.last_valid_index()]
    return (latest_price - years_back_price) / years_back_price

def get_avg_roi_for_years(years_back, df):


while(True):
    now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # update databases
    if now.weekday() <= 4 and now.time() > start.time():
        for ex in exchanges:
            ex_df = pd.DataFrame(columns=[
                                        'symbol',
                                        'exchange',
                                        'year_one_roi_total',
                                        'year_two_roi_total',
                                        'year_two_roi_avg',
                                        'year_three_roi_total',
                                        'year_three_roi_avg',
                                        'year_four_roi_total',
                                        'year_four_roi_avg',
                                        'year_eight_roi_total',
                                        'year_eight_roi_avg',
                                        'year_twelve_roi_total',
                                        'year_twelve_roi_avg',
                                        'year_sixteen_roi_total',
                                        'year_sixteen_roi_avg',
                                        'year_twenty_roi_total',
                                        'year_twenty_roi_avg',
                                        'last_updated',
                                        ])
            symbols_json = get_all_exchange_symbols(ex)
            symbols_dict = ['gaw']#json.loads(symbols_json)  # obj now contains a dict of the data
            for symbol in symbols_dict:
                raw_data = json.loads(get_eod_for_symbol(symbol, ex)) # switch symbol with symbol['Code]
                df = pd.DataFrame(raw_data)
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')['close']

                year_one_roi = get_total_roi_for_years(1, df)
                year_two_roi_total = get_total_roi_for_years(2, df)
                year_three_roi_total = get_total_roi_for_years(3, df)
                year_four_roi_total = get_total_roi_for_years(4, df)
                year_eight_roi_total = get_total_roi_for_years(8, df)
                year_twelve_roi_total = get_total_roi_for_years(12, df)
                year_sixteen_roi_total = get_total_roi_for_years(16, df)
                year_twenty_roi_total = get_total_roi_for_years(20, df)
                total_roi = get_total_roi(df)

                year_two_roi_avg = get_avg_roi_for_years(2, df)
                year_three_roi_avg = get_avg_roi_for_years(3, df)
                year_four_roi_avg = get_avg_roi_for_years(4, df)
                year_eight_roi_avg = get_avg_roi_for_years(8, df)
                year_twelve_roi_avg = get_avg_roi_for_years(12, df)
                year_sixteen_roi_avg = get_avg_roi_for_years(16, df)
                year_twenty_roi_avg = get_avg_roi_for_years(20, df)
                avg_roi_total = get_avg_roi_total(df)

                print(year_one_roi_total)
                print(year_two_roi_total)
                print(year_three_roi_total)
                print(year_four_roi_total)
                print(year_eight_roi_total)
                print(year_twelve_roi_total)
                print(year_sixteen_roi_total)
                print(year_twenty_roi_total)

            # Sort the exchange symbols by
                # Calculate total ROI and average ROI for 1,2,3,4,8,12,16,20 years
                # Columns for roi db:
                # id, symbol, exchange, total & avg roi for 1,2,3,4,8,12,16,20 years
                # DataFrame.to_sql in pandas


    # Update metadata on saturday
    #elif now.weekday < 6:

    # Sleep until next closing time for exchange
    # If it is the weekend then being metadata calculations and save in DB

    # Edge cases: for milestones, ignore leap years for 1,2,3 year milestones (use historical Februaury 28th instead if current day is leap year
    # How to synchornize times?
    #time.sleep(0)
    break;