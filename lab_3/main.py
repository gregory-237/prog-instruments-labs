import re
import logging
from typing import Hashable

import pandas as pd

from checksum import calculate_checksum, serialize_result
from config import PATTERNS, CSV_PATH

logging.basicConfig(level=logging.INFO, filename="logs.log", filemode='w')


def read_csv(path: str) -> pd.DataFrame:
    """
    Reading input .csv file into dataframe object
    :param path: (str) .csv file path
    :return raw_data: (pd.DataFrame) output dataframe object
    """
    try:
        raw_data: pd.DataFrame = pd.read_csv(path, sep=";", encoding="utf-16")
        return raw_data
    except Exception as e:
        logging.error(f'Can not read .csv file - {e}')


def row_is_valid(row: pd.Series) -> bool:
    """
    Checking row valid using regular expressions
    :param row: (pd.Series) input row
    :return: (bool) True - valid, False - not valid
    """
    return all(re.match(PATTERNS[key], str(row[key])) for key in PATTERNS if key in row)


def indices_invalid_rows(raw_data: pd.DataFrame) -> list[Hashable]:
    """
    Returning list of indices of invalid rows
    :param raw_data: (pd.DataFrame) input data from .csv file
    :return: (list[Hashable]) list of indices of invalid rows
    """
    return [index for index, row in raw_data.iterrows() if not row_is_valid(row)]


if __name__ == "__main__":
    serialize_result(80, calculate_checksum(indices_invalid_rows(read_csv(CSV_PATH))))

