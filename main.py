# Here shall be written the code that builds my portfolio
# input data and calculate the ROI from different companies and average all the companies to represent the "market"
# look at both the open and the close
# company symbol,ROI per year starting from recent, going back 15 years at the most
# company symbol, ROI past 15 years, ROI past 10 years, ROI past 5 years
# import psycopg2
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
import logging
from sqlalchemy import MetaData
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import timeit

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
exchanges = Constants.EXCHANGES
API_DAILY_LIMIT = 100000


def check_in_later(stop):
    # Check in after an hour
    # Ideally sleep until the next day when there are more api requests avail
    print('I am getting tired, see you after my nap')
    time_before_midnight = stop - datetime.utcnow()
    time.sleep(time_before_midnight.seconds + 10)


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
        return requests.get(
            'https://eodhistoricaldata.com/api/exchanges/%s?api_token=%s&fmt=json' % (exchange, service_key)).text



def get_eod_for_symbol(ticker, exchange, period='d', order='d'):
        return requests.get('https://eodhistoricaldata.com/api/eod/%s.%s?api_token=%s&period=%s&order=%s&fmt=json' % (
            ticker, exchange, service_key, period, order)).text


def avg_helper(roi_list, year):
    sum = 0
    count = 0
    while 0 < year <= len(roi_list):
        year -= 1
        if roi_list[year] is not None:
            sum += roi_list[year]
            count += 1
    if count == 0: return -1
    return sum / count


def get_total_roi_for_years(years_back, pddf):
    latest = pddf.first_valid_index()
    latest_price = pddf[latest]
    return_roi = []
    for year in years_back:
        years_back_date = latest - timedelta(days=year * 365)
        if years_back_date not in pddf.index:
            years_back_date = get_nearest_day(years_back_date, pddf.index)
        if years_back_date < pddf.last_valid_index() or pddf[years_back_date] == 0:
            return_roi.append(-1)
        else:
            years_back_price = pddf[years_back_date]
            return_roi.append((latest_price - years_back_price) / years_back_price)
    return return_roi


def get_total_roi(pddf):
    latest = pddf.first_valid_index()
    latest_price = pddf[latest]
    years_back_price = pddf[pddf.last_valid_index()]
    if years_back_price == 0: return -1
    return (latest_price - years_back_price) / years_back_price


def get_avg_roi_for_years(years_back, pddf):
    every_roi = get_roi_for_every_year(pddf)
    if len(every_roi) == 0: return [-1] * 8
    avg_roi_list = []
    for year in years_back:
        avg_roi_list.append(avg_helper(every_roi, year))

    # Total avg roi for life of the company
    avg_roi_list.append(avg_helper(every_roi, len(every_roi)))
    return avg_roi_list


def get_roi_for_every_year(pddf):
    count = 1
    every_roi = []
    latest = pddf.first_valid_index()
    years_back_date = latest - timedelta(days=count * 365)
    first_entry = pddf.last_valid_index()
    while years_back_date > first_entry:
        latest_date = latest - timedelta(days=(count - 1) * 365)
        years_back_date = latest - timedelta(days=count * 365)
        if years_back_date not in pddf.index:
            years_back_date = get_nearest_day(years_back_date, pddf.index)
        if latest_date not in pddf.index:
            latest_date = get_nearest_day(latest_date, pddf.index)
        latest_price = pddf[latest_date]
        years_back_price = pddf[years_back_date]
        if years_back_price == 0:
            every_roi.append(-1)  # ignore this year when calculating avg
        else:
            every_roi.append((latest_price - years_back_price) / years_back_price)
        count += 1
    return every_roi

def add_table(table_name, pd):
    engine = create_engine(
        'postgresql://' + creds.PGUSER + ':' + creds.PGPASSWORD + '@' + creds.PGHOST + ':' + creds.PGPORT + '/' + creds.PGDATABASE)
    pd.to_sql(table_name, engine)


def drop_table(table_name):
    engine = create_engine(
        'postgresql://' + creds.PGUSER + ':' + creds.PGPASSWORD + '@' + creds.PGHOST + ':' + creds.PGPORT + '/' + creds.PGDATABASE)
    base = declarative_base()
    metadata = MetaData(engine, reflect=True)
    table = metadata.tables.get(table_name)
    if table is not None:
        logging.info('Deleting %s table' % table_name)
        base.metadata.drop_all(engine, [table], checkfirst=True)


def main():
    api_count = 0
    while True:
        tomorrow = datetime.utcnow() + timedelta(days=1)
        program_stop_time = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)

        if True:  # 0 < datetime.utcnow().isoweekday() < 6:
            # Midnight tonight!
            print('Beginning Data Collection')
            # update databases
            for ex in exchanges:
                start_time = timeit.default_timer()
                ex_df = pd.DataFrame(columns=ex_cols)
                print('Accessing info for %s Exchange' % ex)
                if api_count < API_DAILY_LIMIT:
                    symbols_json = get_all_exchange_symbols(ex)
                else:
                    check_in_later(program_stop_time)
                symbols_dict = json.loads(symbols_json)  # obj now contains a dict of the data
                total_length = len(symbols_dict)
                i = 0
                for symbol in symbols_dict:
                    i += 1
                    progress(i, total_length, status='Retrieving Data for %s.%s. %s sec Elapsed. Estimated %s sec' % (
                        symbol['Code'], ex, round(timeit.default_timer() - start_time, 2),
                        round((timeit.default_timer() - start_time) * (total_length - i) / i, 2)))
                    try:
                        if api_count < API_DAILY_LIMIT:
                            raw_data = get_eod_for_symbol(symbol['Code'], ex)
                        else:
                            check_in_later(program_stop_time)
                    except ConnectionError:
                        print(
                            'Connection Error with %s.%s: Going to sleep for 30 seconds before resuming' % (
                                symbol['Code'], ex))
                        time.sleep(15)
                        if api_count < API_DAILY_LIMIT:
                            raw_data = get_eod_for_symbol(symbol['Code'], ex)
                        else:
                            check_in_later(program_stop_time)
                    try:
                        formatted_data = json.loads(raw_data)
                    except ValueError:
                        print('Formatting Error with %s.%s' % (symbol['Code'], ex))
                        time.sleep(15)
                        # recall API
                        if api_count < API_DAILY_LIMIT:
                            raw_data = get_eod_for_symbol(symbol['Code'], ex)
                        else:
                            check_in_later(program_stop_time)
                        formatted_data = json.loads(raw_data)

                    if len(formatted_data) > 0:
                        df = pd.DataFrame(formatted_data)
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.set_index('date')['close']

                        progress(i, total_length,
                                 status='Calculating Data for %s.%s. %s sec Elapsed. Estimated %s sec left' % (
                                     symbol['Code'], ex, round(timeit.default_timer() - start_time, 2),
                                     round((timeit.default_timer() - start_time) * (total_length - i) / i, 2)))
                        year_roi_totals = get_total_roi_for_years([1, 2, 3, 4, 8, 12, 16, 20], df)
                        roi_total = get_total_roi(df)

                        total_roi_avg = get_avg_roi_for_years([2, 3, 4, 8, 12, 16, 20], df)
                        ex_df = ex_df.append(
                            {
                                'symbol': symbol['Code'],
                                'name': symbol['Name'],
                                'country': symbol['Country'],
                                'exchange': ex,
                                'year_one_roi_total': year_roi_totals[0],
                                'year_two_roi_total': year_roi_totals[1],
                                'year_three_roi_total': year_roi_totals[2],
                                'year_four_roi_total': year_roi_totals[3],
                                'year_eight_roi_total': year_roi_totals[4],
                                'year_twelve_roi_total': year_roi_totals[5],
                                'year_sixteen_roi_total': year_roi_totals[6],
                                'year_twenty_roi_total': year_roi_totals[7],
                                'roi_total': roi_total,
                                'year_two_roi_avg': total_roi_avg[0],
                                'year_three_roi_avg': total_roi_avg[1],
                                'year_four_roi_avg': total_roi_avg[2],
                                'year_eight_roi_avg': total_roi_avg[3],
                                'year_twelve_roi_avg': total_roi_avg[4],
                                'year_sixteen_roi_avg': total_roi_avg[5],
                                'year_twenty_roi_avg': total_roi_avg[6],
                                'total_roi_avg': total_roi_avg[7],
                                'last_updated': datetime.utcnow(),
                            }, ignore_index=True
                        )
                    else:
                        print('Data is empty for %s.%s' % (symbol['Code'], ex))

                drop_table(ex + '_roi')
                add_table(ex + '_roi', ex_df)
        else:
            # trigger metadata calculations and sleep till noon on Monday
            print('It is the weekend, see ya Monday fools!')
            after_weekend = datetime.utcnow() + timedelta(days=2)
            weekend_time = datetime(after_weekend.year, after_weekend.month, after_weekend.day, 12, 0,
                                    0) - datetime.utcnow()
            time.sleep(weekend_time.seconds)


main()
