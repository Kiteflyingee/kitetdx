
import unittest
from unittest.mock import patch, MagicMock
import os
import time
import pandas as pd
from kitetdx.sws import SwsReader

class TestSwsReader(unittest.TestCase):
    def setUp(self):
        # Sample DataFrame for mocking load_data
        self.mock_df = pd.DataFrame({
            'stock_code': ['600000', '000001'],
            'stock_name': ['浦发银行', '平安银行'],
            'industry_code': ['480301', '480301'],
            'l1_name': ['银行', '银行'],
            'l2_name': ['股份制银行Ⅱ', '股份制银行Ⅱ'],
            'l3_name': ['股份制银行Ⅲ', '股份制银行Ⅲ']
        })

    @patch('kitetdx.sws.download_sws_data')
    @patch('kitetdx.sws.SwsReader._find_stock_file')
    @patch('kitetdx.sws.os.path.exists')
    @patch('kitetdx.sws.os.path.getmtime')
    @patch('kitetdx.sws.SwsReader._load_data')
    def test_init_fresh_download(self, mock_load, mock_mtime, mock_exists, mock_find, mock_download):
        """Test initialization when no data exists (should download)"""
        mock_exists.return_value = False
        mock_find.return_value = None
        mock_load.return_value = self.mock_df
        
        SwsReader(cache_dir='/tmp/testlimit')
        
        mock_download.assert_called_once()

    @patch('kitetdx.sws.download_sws_data')
    @patch('kitetdx.sws.SwsReader._find_stock_file')
    @patch('kitetdx.sws.os.path.exists')
    @patch('kitetdx.sws.os.path.getmtime')
    @patch('kitetdx.sws.SwsReader._load_data')
    def test_init_valid_cache(self, mock_load, mock_mtime, mock_exists, mock_find, mock_download):
        """Test initialization with valid cache (should NOT download)"""
        mock_exists.return_value = True
        mock_find.return_value = '/tmp/testlimit/file.xlsx'
        # File modified just now
        mock_mtime.return_value = time.time()
        mock_load.return_value = self.mock_df
        
        SwsReader(cache_dir='/tmp/testlimit')
        
        mock_download.assert_not_called()

    @patch('kitetdx.sws.download_sws_data')
    @patch('kitetdx.sws.SwsReader._find_stock_file')
    @patch('kitetdx.sws.os.path.exists')
    @patch('kitetdx.sws.os.path.getmtime')
    @patch('kitetdx.sws.SwsReader._load_data')
    def test_init_expired_cache(self, mock_load, mock_mtime, mock_exists, mock_find, mock_download):
        """Test initialization with expired cache > 90 days (should download)"""
        mock_exists.return_value = True
        mock_find.return_value = '/tmp/testlimit/file.xlsx'
        # File modified 91 days ago
        mock_mtime.return_value = time.time() - (91 * 86400)
        mock_load.return_value = self.mock_df
        
        SwsReader(cache_dir='/tmp/testlimit')
        
        # Should initiate download
        mock_download.assert_called_once()

    @patch('kitetdx.sws.download_sws_data')
    @patch('kitetdx.sws.SwsReader._find_stock_file')
    @patch('kitetdx.sws.os.path.exists')
    @patch('kitetdx.sws.os.path.getmtime')
    @patch('kitetdx.sws.SwsReader._load_data')
    def test_force_update(self, mock_load, mock_mtime, mock_exists, mock_find, mock_download):
        """Test force_update=True (should download regardless of cache)"""
        mock_exists.return_value = True
        mock_find.return_value = '/tmp/testlimit/file.xlsx'
        mock_mtime.return_value = time.time() # Fresh file
        mock_load.return_value = self.mock_df
        
        SwsReader(cache_dir='/tmp/testlimit', force_update=True)
        
        mock_download.assert_called_once()

    @patch('kitetdx.sws.SwsReader._load_data')
    @patch('kitetdx.sws.SwsReader._find_stock_file') # Bypass file check for query tests
    @patch('kitetdx.sws.os.path.getmtime') # Mock mtime to avoid FileNotFoundError
    @patch('kitetdx.sws.os.path.exists')
    def test_data_query(self, mock_exists, mock_mtime, mock_find, mock_load):
        """Test get_industries and get_stock_industry"""
        mock_exists.return_value = True
        mock_find.return_value = '/fake/path'
        mock_mtime.return_value = time.time()
        mock_load.return_value = self.mock_df
        
        reader = SwsReader(cache_dir='/fake', auto_download=False)
        
        # Test get_industries
        l1 = reader.get_industries(level=1)
        self.assertEqual(l1, ['银行'])
        
        # Test get_stock_industry
        info = reader.get_stock_industry('600000')
        self.assertEqual(info['stock_name'], '浦发银行')
        self.assertEqual(info['l1_name'], '银行')

if __name__ == '__main__':
    unittest.main()
