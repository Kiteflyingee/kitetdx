import pytest
from unittest.mock import MagicMock, patch
from kitetdx import Quotes

class TestQuotes:
    def test_factory(self):
        with patch('mootdx.quotes.Quotes.factory') as mock_factory:
            Quotes.factory(market='std')
            mock_factory.assert_called_once_with(market='std')

    def test_bars_delegation(self):
        with patch('mootdx.quotes.Quotes.factory') as mock_factory:
            mock_client = MagicMock()
            mock_factory.return_value = mock_client
            
            client = Quotes(market='std')
            client.bars(symbol='600036')
            
            mock_client.bars.assert_called_once()

    def test_finance_delegation(self):
        with patch('mootdx.quotes.Quotes.factory') as mock_factory:
            mock_client = MagicMock()
            mock_factory.return_value = mock_client
            
            client = Quotes(market='std')
            client.finance(symbol='600036')
            
            mock_client.finance.assert_called_once_with(symbol='600036')
