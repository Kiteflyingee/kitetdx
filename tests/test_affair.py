import pytest
from unittest.mock import patch
from kitetdx import Affair

class TestAffair:
    def test_files_delegation(self):
        with patch('mootdx.affair.Affair.files') as mock_files:
            Affair.files()
            mock_files.assert_called_once()

    def test_fetch_delegation(self):
        with patch('mootdx.affair.Affair.fetch') as mock_fetch:
            Affair.fetch(downdir='tmp', filename='test.zip')
            mock_fetch.assert_called_once_with(downdir='tmp', filename='test.zip')
