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

    def test_avg_helper(self):
        pass

    @data(
        (datetime(2010, 10, 10),
         datetime(2010, 10, 11),
         pd.Index(
            [
                datetime(2010, 10, 11),
                datetime(2010, 10, 12),
                datetime(2010, 9, 10)
            ]
        )
         ),
        (datetime(2010, 1, 1),
         datetime(2010, 2, 10),
         pd.Index(
            [
                datetime(2009, 12, 30),
                datetime(2010, 10, 12),
                datetime(2010, 2, 10)
            ]
        )
         )
    )
    def test_get_nearest_day(self, params):
        test_day, exp_result, test_index = params
        result = main.get_nearest_day(test_day, test_index)
        self.assertEqual(result, exp_result)


    def test_get_total_roi_for_years(self):
        pass

    def test_get_total_roi(self):
        pass

    def test_get_avg_roi_for_years(self):
        pass

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
