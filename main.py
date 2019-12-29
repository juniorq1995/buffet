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
from requests.exceptions import ConnectionError
import time
import Constants
from datetime import date, datetime, timedelta
import json
from sqlalchemy import create_engine

ex_cols = [
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
]
service_key = Constants.EOD_API_TOKEN
exchanges = ['US']

def progress(count, total, status=''):
    bar_len = 100
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()

def get_nearest_day(missing_day, idx):
    while missing_day not in idx:
        missing_day = missing_day + timedelta(days=1)
    return missing_day
def get_all_exchange_symbols(exchange):
    # API return format is:
    # {"Code":"XXX", "Name": "X", "Country": "USA", "Exchange": "NASDAQ", "Currency": "USD", "Type": "Common Stock"},
    return requests.get('https://eodhistoricaldata.com/api/exchanges/%s?api_token=%s&fmt=json' % (exchange, service_key)).text

def get_eod_for_symbol(ticker, exchange, period='d', order='d'):
    return requests.get('https://eodhistoricaldata.com/api/eod/%s.%s?api_token=%s&period=%s&order=%s&fmt=json' % (ticker, exchange, service_key, period, order)).text

def connect_to_db():
    conn_string = "host=" + creds.PGHOST + " port=" + "5432" + " dbname=" + creds.PGDATABASE + " user=" + creds.PGUSER \
                  + " password=" + creds.PGPASSWORD
    conn = psycopg2.connect(conn_string)

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
    count = 1
    latest = pddf.first_valid_index()
    years_back_date = latest - timedelta(days=count * 365)
    first_entry = pddf.last_valid_index()
    while years_back_date > first_entry:
        latest_date = latest - timedelta(days=(count-1) * 365)
        years_back_date = latest - timedelta(days=count * 365)
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

while True:
    print('Beginning Data Collection')
    now = datetime.now() # Change to a select ime later
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # update databases
    if now.weekday() <= 6 and now.time() > start.time(): # Change weekday back to 4
        for ex in exchanges:
            symbols_json = get_all_exchange_symbols(ex)
            symbols_dict = json.loads(symbols_json)  # obj now contains a dict of the data
            ex_df = pd.DataFrame(columns=ex_cols)
            print('Accessing info for %s Exchange' % ex)
            total = len(symbols_dict)
            i = 0
            for symbol in symbols_dict:
                i+=1
                #print('Now getting data for %s.%s' % (symbol, ex))# switch symbol with symbol['Code]
                progress(i, total, status='Now getting data for %s.%s' % (symbol['Code'], ex))
                try:
                    raw_data = get_eod_for_symbol(symbol['Code'], ex)# switch symbol with symbol['Code]
                except ConnectionError:
                    print('Connection Error: Going to sleep for 30 seconds before resuming')
                    time.sleep(15)
                    raw_data = get_eod_for_symbol(symbol['Code'], ex)
                try:
                    formatted_data = json.loads(raw_data)
                except ValueError:
                    print('Formatting Error')
                    time.sleep(15)
                    # recall API
                    raw_data = get_eod_for_symbol(symbol['Code'], ex)  # switch symbol with symbol['Code]
                    formatted_data = json.loads(raw_data)

                if len(formatted_data) > 0:
                    df = pd.DataFrame(formatted_data)
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date')['close']

                    progress(i, total, status='Calculating Data')
                    year_one_roi_total = get_total_roi_for_years(1, df)
                    year_two_roi_total = get_total_roi_for_years(2, df)
                    year_three_roi_total = get_total_roi_for_years(3, df)
                    year_four_roi_total = get_total_roi_for_years(4, df)
                    year_eight_roi_total = get_total_roi_for_years(8, df)
                    year_twelve_roi_total = get_total_roi_for_years(12, df)
                    year_sixteen_roi_total = get_total_roi_for_years(16, df)
                    year_twenty_roi_total = get_total_roi_for_years(20, df)
                    roi_total = get_total_roi(df)

                    year_two_roi_avg = get_avg_roi_for_years(2, df)
                    year_three_roi_avg = get_avg_roi_for_years(3, df)
                    year_four_roi_avg = get_avg_roi_for_years(4, df)
                    year_eight_roi_avg = get_avg_roi_for_years(8, df)
                    year_twelve_roi_avg = get_avg_roi_for_years(12, df)
                    year_sixteen_roi_avg = get_avg_roi_for_years(16, df)
                    year_twenty_roi_avg = get_avg_roi_for_years(20, df)
                    total_roi_avg = get_avg_roi_total(df)
                    ex_df = ex_df.append(
                        {
                            'symbol':symbol,
                            'exchange': ex,
                            'year_one_roi_total': year_one_roi_total,
                            'year_two_roi_total': year_two_roi_total,
                            'year_three_roi_total': year_three_roi_total,
                            'year_four_roi_total': year_four_roi_total,
                            'year_eight_roi_total': year_eight_roi_total,
                            'year_twelve_roi_total': year_twelve_roi_total,
                            'year_sixteen_roi_total': year_sixteen_roi_total,
                            'year_twenty_roi_total': year_twenty_roi_total,
                            'roi_total': roi_total,
                            'year_two_roi_avg': year_two_roi_avg,
                            'year_three_roi_avg': year_three_roi_avg,
                            'year_four_roi_avg': year_four_roi_avg,
                            'year_eight_roi_avg': year_eight_roi_avg,
                            'year_twelve_roi_avg': year_twelve_roi_avg,
                            'year_sixteen_roi_avg': year_sixteen_roi_avg,
                            'year_twenty_roi_avg': year_twenty_roi_avg,
                            'total_roi_avg': total_roi_avg,
                            'last_updated': datetime.utcnow(),
                        }, ignore_index=True
                    )
                else:
                    print('Data is empty')

        engine = create_engine('postgresql://' + creds.PGUSER + ':' + creds.PGPASSWORD + '@'+creds.PGHOST + ':'+ creds.PGPORT + '/' + creds.PGDATABASE)
        ex_df.to_sql(ex + '_roi', engine)

    #time.sleep(0)


    break