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

ex_cols = (
    'symbol',
    'exchange',
    'year_one_roi_total',
    'year_two_roi_total',
    'year_three_roi_total',
    'year_four_roi_total',
    'year_eight_roi_total',
    'year_twelve_roi_total',
    'year_sixteen_roi_total',
    'year_twenty_roi_total',
    'roi_total',
    'year_two_roi_avg',
    'year_three_roi_avg',
    'year_four_roi_avg',
    'year_eight_roi_avg',
    'year_twelve_roi_avg',
    'year_sixteen_roi_avg',
    'year_twenty_roi_avg',
    'total_roi_avg',
    'last_updated',
)
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

def get_total_roi_for_years(years_back, pddf):
    latest = pddf.first_valid_index()
    latest_price = pddf[latest]
    years_back_date = latest - timedelta(days=years_back*365)
    if years_back_date not in pddf.index:
        years_back_date = get_nearest_day(years_back_date, df.index)
    if years_back_date < pddf.last_valid_index():
        return None
    years_back_price = pddf[years_back_date]
    return (latest_price - years_back_price) / years_back_price

def get_total_roi(pddf):
    latest = pddf.first_valid_index()
    latest_price = pddf[latest]
    years_back_price = pddf[pddf.last_valid_index()]
    return (latest_price - years_back_price) / years_back_price

def get_avg_roi_for_years(years_back, pddf):
    total = 0
    count = 0
    latest = pddf.first_valid_index()
    while years_back >= count:
        latest_date = latest - timedelta(days=count * 365)
        years_back_date = latest - timedelta(days=(count+1) * 365)
        if years_back_date not in pddf.index:
            years_back_date = get_nearest_day(years_back_date, pddf.index)
        if latest_date not in pddf.index:
            latest_date = get_nearest_day(latest_date, pddf.index)
        if years_back_date < pddf.last_valid_index():
            return None
        latest_price = pddf[latest_date]
        years_back_price = pddf[years_back_date]
        roi = (latest_price - years_back_price) / years_back_price
        total += roi
        count+=1
    return total / years_back

def get_avg_roi_total(pddf):
    total = 0
    count = 0
    latest = pddf.first_valid_index()
    years_back_date = latest - timedelta(days=(count + 1) * 365)
    first_entry = pddf.last_valid_index()
    while years_back_date > first_entry:
        latest_date = latest - timedelta(days=count * 365)
        years_back_date = latest - timedelta(days=(count + 1) * 365)
        if years_back_date not in pddf.index:
            years_back_date = get_nearest_day(years_back_date, pddf.index)
        if latest_date not in pddf.index:
            latest_date = get_nearest_day(latest_date, pddf.index)
        latest_price = pddf[latest_date]
        years_back_price = pddf[years_back_date]
        roi = (latest_price - years_back_price) / years_back_price
        total += roi
        count += 1
    return total / count

while(True):
    now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # update databases
    if now.weekday() <= 4 and now.time() > start.time():
        for ex in exchanges:
            #ex_df = pd.DataFrame(columns=ex_cols)
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

    #time.sleep(0)
                try:
                    connection = psycopg2.connect(user=creds.PGUSER,
                                                  password=creds.PGPASSWORD,
                                                  host=creds.PGHOST,
                                                  port=creds.PGPORT,
                                                  database=creds.PGDATABASE)
                    cursor = connection.cursor()

                    postgres_insert_query = """ INSERT INTO %s (
                        symbol,
                        exchange,
                        year_one_roi_total,
                        year_two_roi_total,
                        year_three_roi_total,
                        year_four_roi_total,
                        year_eight_roi_total,
                        year_twelve_roi_total,
                        year_sixteen_roi_total,
                        year_twenty_roi_total,
                        roi_total,
                        year_two_roi_avg,
                        year_three_roi_avg,
                        year_four_roi_avg,
                        year_eight_roi_avg,
                        year_twelve_roi_avg,
                        year_sixteen_roi_avg,
                        year_twenty_roi_avg,
                        total_roi_avg,
                        last_updated,) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                    record_to_insert = (ex + '_roi', symbol, ex,
                                        year_one_roi,
                                        year_two_roi,
                                        year_three_roi,
                                        year_four_roi,
                                        year_eight_roi,
                                        year_twelve_roi,
                                        year_sixteen_roi,
                                        year_twenty_roi,
                                        total_roi,
                                        year_two_roi_avg,
                                        year_three_roi_avg,
                                        year_four_roi_avg,
                                        year_eight_roi_avg,
                                        year_twelve_roi_avg,
                                        year_sixteen_roi_avg,
                                        year_twenty_roi_avg,
                                        avg_roi_total)
                    cursor.execute(postgres_insert_query, record_to_insert)

                    connection.commit()
                    count = cursor.rowcount
                    print (count, "Record inserted successfully into mobile table")
                    if connection:
                        cursor.close()
                        connection.close()
                        print("PostgreSQL connection is closed")

                except (Exception, psycopg2.Error) as error:
                    print("Failed to connect to table", error)

    break