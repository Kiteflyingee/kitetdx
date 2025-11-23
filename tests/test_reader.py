import pytest
from unittest.mock import MagicMock, patch
from kitetdx import Reader
from kitetdx.entities import Stock, Concept

class TestReader:
    def test_factory(self):
        # Test factory creation
        with patch('pathlib.Path.is_dir', return_value=True):
            reader = Reader.factory(market='std', tdxdir='/tmp/tdx')
            assert reader is not None

    def test_daily_mock(self):
        # Mock the internal reader and file existence
        with patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('mootdx.contrib.compat.MooTdxDailyBarReader.get_df', return_value='mock_df'), \
             patch('kitetdx.reader.to_data', return_value='processed_df'):
            
            reader = Reader.factory(market='std', tdxdir='/tmp/tdx')
            # Mock find_path to return a dummy path
            reader.find_path = MagicMock(return_value='/tmp/tdx/vipdoc/sh/lday/sh600036.day')
            
            result = reader.daily('600036')
            assert result == 'processed_df'

    def test_block_parsing(self):
        # Test the custom block parsing logic with mocked data
        with patch('pathlib.Path.is_dir', return_value=True), \
             patch('kitetdx.reader.read_data') as mock_read:
            
            # Mock stock mapping file
            # Mock block data file
            def side_effect(path):
                if 'infoharbor_ex.code' in str(path):
                    return ['600036|招商银行|ZSYH']
                if 'infoharbor_block.dat' in str(path):
                    return [
                        '#GN_银行_001',
                        '1#600036',
                        '#GN_保险_002',
                        '1#601318'
                    ]
                return []
            
            mock_read.side_effect = side_effect
            
            reader = Reader.factory(market='std', tdxdir='/tmp/tdx')
            concepts = reader.block()
            
            assert len(concepts) == 2
            assert concepts[0].concept_name == '银行'
            assert concepts[0].stocks[0].stock_code == '600036'
            assert concepts[0].stocks[0].stock_name == '招商银行'
