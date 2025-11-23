from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Stock:
    exchange: str  # '0','1','2'
    stock_code: str
    stock_name: Optional[str] = None

    @property
    def full_code(self):
        exchange_map = {'0': 'sz', '1': 'sh', '2': 'bj'}
        return f"{exchange_map.get(self.exchange, '')}{self.stock_code}"


@dataclass
class Concept:
    concept_type: str  # 'GN','FG','ZS'
    concept_name: str
    concept_code: str
    stocks: List[Stock]

    def __init__(self, concept_type: str, concept_name: str, concept_code: str):
        self.concept_type = concept_type
        self.concept_name = concept_name
        self.concept_code = concept_code
        self.stocks = []
