# Here shall be written the code that builds my portfolio
# input data and calculate the ROI from different companies and average all the companies to represent the "market"
# look at both the open and the close
# company symbol,ROI per year starting from recent, going back 15 years at the most
# company symbol, ROI past 15 years, ROI past 10 years, ROI past 5 years
# import psycopg2
import sys
import pandas as pd
import example_psql as creds
import requests
from requests.exceptions import ConnectionError
import time
import Constants
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy import MetaData
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import timeit

service_key = Constants.EOD_API_TOKEN
exchanges = Constants.EXCHANGES
exchange_cols = Constants.EX_COLS
API_DAILY_LIMIT = 100000  # 100,000
API_COUNT = 0  # Global Counter Variable


def hibernate(num_days):
    """
    Puts processes to sleep for X days

    :param num_days: Number of days to sleep
    :type num_days: Integer
    :return: No Return
    """

    print('It is the weekend, see ya Monday fools!')
    wake_time = datetime.utcnow() + timedelta(days=num_days)
    sleep_time = datetime(wake_time.year, wake_time.month, wake_time.day, 12, 0,
                          0) - datetime.utcnow()
    time.sleep(sleep_time.seconds)


def sleep_api_limit_reset():
    """
    A simple function that puts the system to sleep until UTC midnight when the
    API limit is reset
    :return:
    """

    # Check in after an hour
    # Ideally sleep until the next day when there are more api requests avail
    print('I am getting tired, see you after my nap')
    global API_COUNT
    API_COUNT = 0
    tomorrow = datetime.utcnow() + timedelta(days=1)
    program_stop_time = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
    time_before_midnight = program_stop_time - datetime.utcnow()
    time.sleep(time_before_midnight.seconds + 10)


def progress(count, total, status=''):
    """
    Calculatues what percentage of the current task ahs been completed and
    outputs it in a progress bar to stdout

    :param count: Which company the program is currently on
    :type count: Integer
    :param total: The total number of companies for an exchange
    :type total: Integer
    :param status: string progress bar
    :type status: String
    :return: No return, writes status to stdout
    """

    bar_len = 100
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()


def get_nearest_day(missing_day, idx):
    """


    :param missing_day: datetime.datetime
    :param idx: pandas.core.indexes.datetimes.DatetimeIndex
    :return:
    """

    while missing_day not in idx:
        missing_day = missing_day + timedelta(days=1)
    return missing_day


def get_all_exchange_symbols(exchange):
    """

    :param exchange:
    :return:
    """

    # API return format is:
    # {"Code":"XXX", "Name": "X", "Country": "USA", "Exchange": "NASDAQ", "Currency": "USD", "Type": "Common Stock"},
    global API_COUNT
    if API_COUNT > API_DAILY_LIMIT:
        sleep_api_limit_reset()
    API_COUNT += 1
    return requests.get(
        'https://eodhistoricaldata.com/api/exchanges/%s?api_token=%s&fmt=json' % (exchange, service_key)).text


def get_eod_for_symbol(ticker, exchange, period='d', order='d'):
    """
    Makes an API call for all EOD data for a specified company in a
    specified exchange

    :param ticker: Company ticker symbol
    :param exchange: Securities Exchange symbol
    :param period:
    :param order:
    :return:
    """
    global API_COUNT
    if API_COUNT > API_DAILY_LIMIT:
        sleep_api_limit_reset()
    API_COUNT += 1
    return requests.get('https://eodhistoricaldata.com/api/eod/%s.%s?api_token=%s&period=%s&order=%s&fmt=json' % (
        ticker, exchange, service_key, period, order)).text


def avg_helper(roi_list, year):
    """

    :param roi_list: List of ROI for each year
    :type roi_list: List
    :param year: Number of years to go back in EOD data, Index
    :type year: Integer
    :return: Float Avg
    """

    sum = 0
    count = 0
    while 0 < year <= len(roi_list):
        year -= 1
        if roi_list[year] is not None:
            sum += roi_list[year]
            count += 1
    return -1 if count == 0 else sum/float(count)


def get_total_roi_for_years(years_back, pddf):
    """

    :param years_back:
    :type years_back: List of Integers
    :param pddf: Pandas Series containing EOD Data
    :type pddf: pandas.core.series.Series
    :return: List or ROIs
    """

    latest = pddf.first_valid_index() # type is date
    latest_price = pddf[latest]
    return_roi = []
    for year in years_back:
        years_back_date = latest.replace(year=latest.year - year)
        print(years_back_date)
        if years_back_date not in pddf.index:
            years_back_date = get_nearest_day(years_back_date, pddf.index)
        if years_back_date < pddf.last_valid_index() or pddf[years_back_date] == 0:
            return_roi.append(-1)
        else:
            years_back_price = pddf[years_back_date]
            return_roi.append((latest_price - years_back_price) / float(years_back_price))
    return return_roi


def get_total_roi(pddf):
    """

    :param pddf:
    :return:
    """

    latest = pddf.first_valid_index()
    latest_price = pddf[latest]
    years_back_price = pddf[pddf.last_valid_index()]
    if years_back_price == 0: return -1
    return (latest_price - years_back_price) / years_back_price


def get_avg_roi_for_years(years_back, pddf):
    """
    Get the average roi for a range of years

    :param years_back: list of years to get avg for
    :type years_back: list of Integers
    :param pddf: dataframe holding EOD data
    :type pddf: Pandas Dataframe
    :return: List of avg roi for
    """

    # This can be dramatically sped up using the "window" method
    # Simply read the entry from the db, remove the last day and add in new day
    # Need to store dates of the time windows (begin, end)
    every_roi = get_roi_for_every_year(pddf)
    if len(every_roi) == 0: return [-1] * 8
    avg_roi_list = []
    for year in years_back:
        avg_roi_list.append(avg_helper(every_roi, year))

    # Total avg roi for life of the company
    avg_roi_list.append(avg_helper(every_roi, len(every_roi)))
    return avg_roi_list


def get_roi_for_every_year(pddf):
    """

    :param pddf: Dataframe containing EOD data
    :type pddf: Pandas Dataframe
    :return: List of ROI starting from 0 to last year
    """

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
    """

    :param table_name:
    :param pd:
    :return:
    """

    engine = create_engine(
        'postgresql://' + creds.PGUSER + ':' + creds.PGPASSWORD + '@' + creds.PGHOST + ':' + creds.PGPORT + '/' + creds.PGDATABASE)
    pd.to_sql(table_name, engine)


def drop_table(table_name):
    """

    :param table_name:
    :return:
    """

    engine = create_engine(
        'postgresql://' + creds.PGUSER + ':' + creds.PGPASSWORD + '@' + creds.PGHOST + ':' + creds.PGPORT + '/' + creds.PGDATABASE)
    base = declarative_base()
    metadata = MetaData(engine, reflect=True)
    table = metadata.tables.get(table_name)
    if table is not None:
        logging.info('Deleting %s table' % table_name)
        base.metadata.drop_all(engine, [table], checkfirst=True)


def get_formatted_eod_data(symbol, exchange):
    """
    Retrieve and format eod data for a securiy in an exchange
    :param symbol:
    :param exchange:
    :return:
    """

    try:
        raw_data = get_eod_for_symbol(symbol['Code'], exchange)

    except ConnectionError:
        print(
            'Connection Error with %s.%s: Going to sleep for 10 seconds before resuming' % (
                symbol['Code'], exchange))
        time.sleep(10)
        raw_data = get_eod_for_symbol(symbol['Code'], exchange)
    try:
        formatted_data = json.loads(raw_data)
    except ValueError:
        print('Formatting Error with %s.%s' % (symbol['Code'], exchange))
        time.sleep(10)
        # recall API
        raw_data = get_eod_for_symbol(symbol['Code'], exchange)
        formatted_data = json.loads(raw_data)
    return formatted_data


def create_metadata_table_entry(symbol, ex, year_roi_totals, roi_total, total_roi_avg):
    """

    :param symbol:
    :param ex:
    :param year_roi_totals:
    :param roi_total:
    :param total_roi_avg:
    :return:
    """
    return {
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
    }


def create_formatted_dict(data):
    """

    :param data:
    :return: Formatted Dictionary
    """
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df.set_index('date')['close']


def get_symbol_metadata(symbol, ex):
    """

    :param ex:
    :param symbol:
    :return:
    """

    formatted_data = get_formatted_eod_data(symbol, ex)
    row = {}
    if len(formatted_data) > 0:
        df = create_formatted_dict(formatted_data)

        year_roi_totals = get_total_roi_for_years([1, 2, 3, 4, 8, 12, 16, 20], df)
        roi_total = get_total_roi(df)

        total_roi_avg = get_avg_roi_for_years([2, 3, 4, 8, 12, 16, 20], df)

        row = create_metadata_table_entry(symbol, ex, year_roi_totals, roi_total, total_roi_avg)
    else:
        print('Data is empty for %s.%s' % (symbol['Code'], ex))

    return row


def calculate_security_metadata(exchange):
    """
    Collects and calculates metadata about securities in database each day

    :return: New metadata entry for each securities exchange
    """

    start_time = timeit.default_timer()
    ex_df = pd.DataFrame(columns=exchange_cols)
    print('Accessing info for %s Exchange' % exchange)
    symbols_json = get_all_exchange_symbols(exchange)
    symbols_dict = json.loads(symbols_json)  # obj now contains a dict of the data
    total_length = len(symbols_dict)
    count = 0
    for symbol in symbols_dict:
        count += 1
        ex_df.append(get_symbol_metadata(symbol, exchange),
                     ignore_index=True)
        # Update the progress bar
        progress(count, total_length,
                 status='Calculating Data for %s.%s. %s sec Elapsed. Estimated %s sec left' % (
                     symbol['Code'], exchange, round(timeit.default_timer() - start_time, 2),
                     round((timeit.default_timer() - start_time) * (total_length - count) / count, 2)))
    return ex_df


def update_all_metadata_tables():
    """
    Retrieves the metadata for all security exchanges and writes it
    to their respective tables
    :return:
    """

    print('Beginning Data Collection')
    # update databases
    for ex in exchanges:
        new_data = calculate_security_metadata(ex)
        drop_table(ex + '_roi')
        add_table(ex + '_roi', new_data)


if __name__ == '__main__':
    while True:
        if 0 < datetime.utcnow().isoweekday() <= 7:
            update_all_metadata_tables()
        else:
            # trigger metadata calculations and sleep till noon on Monday
            hibernate(2)
