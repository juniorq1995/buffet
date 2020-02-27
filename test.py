import unittest
import main
from ddt import ddt, data, file_data, unpack
from datetime import datetime, timedelta
import pandas as pd

# Here shall lie the test suite
# need to import mock


@ddt
class TestHelperMethods(unittest.TestCase):
    """
    A suite for testing the helper methods
    """
    @data((2, 1.5, [1, 2]), (3, 2, [1, 2, 3]), (4, 2.5, [1, 2, 3, 4]))
    def test_avg_helper(self, params):
        test_years, exp_result, test_list = params
        result = main.avg_helper(test_list, test_years)
        self.assertEqual(result, exp_result)

    @data((datetime(2010, 10, 10), datetime(2010, 10, 11),
           pd.Index([
               datetime(2010, 10, 11),
               datetime(2010, 10, 12),
               datetime(2010, 9, 10)
           ])), (datetime(2010, 1, 1), datetime(2010, 2, 10),
                 pd.Index([
                     datetime(2009, 12, 30),
                     datetime(2010, 10, 12),
                     datetime(2010, 2, 10)
                 ])))
    def test_get_nearest_day(self, params):
        test_day, exp_result, test_index = params
        result = main.get_nearest_day(test_day, test_index)
        self.assertEqual(result, exp_result)

    @data((
        [1, 3, 7, 15],
        [1, 2, 3, 4],
        [100, 50, 25, 12.5, 6.25],
        [
            datetime(2010, 10, 10),
            datetime(2009, 10, 10),
            datetime(2008, 10, 10),
            datetime(2007, 10, 10),
            datetime(2006, 10, 10)
        ],
    ))
    def test_get_total_roi_for_years(self, params):
        exp_result, test_list, data, df_index = params
        test_df = pd.Series(data, index=df_index)
        result = main.get_total_roi_for_years(test_list, test_df)
        self.assertEqual(result, exp_result)

    @data((
        15,
        [100, 50, 25, 12.5, 6.25],
        [
            datetime(2010, 10, 10),
            datetime(2009, 10, 10),
            datetime(2008, 10, 10),
            datetime(2007, 10, 10),
            datetime(2006, 10, 10)
        ],
    ))
    def test_get_total_roi(self, params):
        exp_result, data, df_index = params
        test_df = pd.Series(data, index=df_index)
        result = main.get_total_roi(test_df)
        self.assertEqual(result, exp_result)

    @data()
    def test_get_avg_roi_for_years(self):
        pass

    @data()
    def test_get_roi_for_every_year(self):
        pass


class TestMetadataMethods(unittest.TestCase):
    """
    A suite for testing the methods that retrieve data from the API or write to a DB
    """
    def test_calculate_security_metadata(self):
        pass

    def test_get_symbol_metadata(self):
        pass

    def test_get_formatted_eod_data(self):
        pass

    def test_update_all_metadata_tables(self):
        pass


if __name__ == '__main__':
    unittest.main()
