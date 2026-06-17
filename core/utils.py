import logging
import threading
import re
from datetime import date, datetime
from typing import Any, Dict, Optional, Union, List, Tuple, Callable
from hashlib import sha256
from functools import lru_cache

from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect
from django_htmx.http import HttpResponseClientRedirect, retarget

from ethiopian_date import EthiopianDateConverter

# Configure logger
logger = logging.getLogger(__name__)

# ============================================================================
# Thread-local user management
# ============================================================================

_thread_locals = threading.local()


def set_current_user(user):
    """Set the current user in thread-local storage."""
    _thread_locals.user = user


def get_current_user():
    """
    Get the current user from thread-local storage.
    
    Returns:
        User object or None if not set
    """
    return getattr(_thread_locals, "user", None)


def remove_current_user():
    """Remove the current user from thread-local storage."""
    _thread_locals.user = None


# ============================================================================
# Hashing utilities
# ============================================================================

def hash_sha256(pin: str) -> str:
    """
    Hash a PIN using SHA-256 and return uppercase hex digest.
    
    Args:
        pin: PIN string to hash
        
    Returns:
        Uppercase SHA-256 hash
    """
    if not isinstance(pin, str):
        pin = str(pin)
    
    h = sha256()
    h.update(bytes(pin, encoding="utf-8"))
    return h.hexdigest().upper()


# ============================================================================
# File storage
# ============================================================================

class OverwriteStorage(FileSystemStorage):
    """
    Custom storage class that overwrites existing files instead of renaming.
    """
    
    def get_available_name(self, name: str, max_length: int = None) -> str:
        """
        Delete existing file and return the same name.
        
        Args:
            name: File name
            max_length: Maximum length for the filename
            
        Returns:
            The same filename (after deleting existing file)
        """
        if self.exists(name):
            logger.info(f"Overwriting existing file: {name}")
            self.delete(name)
        return name


# ============================================================================
# Phone number utilities
# ============================================================================

def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize Ethiopian phone numbers to international format (251...).
    
    Examples:
        >>> normalize_phone_number("0912345678")
        '251912345678'
        >>> normalize_phone_number("912345678")
        '251912345678'
        >>> normalize_phone_number("251912345678")
        '251912345678'
    
    Args:
        phone_number: Phone number in various formats
        
    Returns:
        Normalized phone number with 251 prefix
    """
    if not phone_number or not isinstance(phone_number, str):
        return phone_number or ""
    
    # Remove any non-digit characters
    cleaned = re.sub(r'\D', '', phone_number)
    
    # Handle different formats
    if len(cleaned) == 12 and cleaned.startswith('251'):
        return cleaned
    elif len(cleaned) == 10 and cleaned.startswith('0'):
        return '251' + cleaned[1:]
    elif len(cleaned) == 9:
        return '251' + cleaned
    else:
        # Return as-is if format unknown
        logger.warning(f"Unexpected phone number format: {phone_number}")
        return phone_number


# ============================================================================
# Ethiopian date conversion utilities
# ============================================================================

@lru_cache(maxsize=128)
def gregorian_year_to_ethiopian(year: int) -> int:
    """
    Convert a Gregorian year to the corresponding Ethiopian year.
    
    Original logic: EthiopianDateConverter.to_ethiopian(year, 1, 1)[0] + 1
    
    This function handles different return types from the ethiopian-date library
    (tuple vs date object) and provides fallback calculations.
    
    Examples:
        >>> gregorian_year_to_ethiopian(2024)
        2017  # Exact value depends on the library
    
    Args:
        year: Gregorian year (e.g., 2024)
    
    Returns:
        Ethiopian year
    
    Raises:
        ValueError: If year is invalid
    """
    # Input validation
    if not isinstance(year, int):
        raise ValueError(f"Year must be an integer, got {type(year).__name__}")
    
    if year < 1900 or year > 2100:
        logger.warning(f"Year {year} is outside typical range (1900-2100)")
    
    try:
        # Convert January 1st of the Gregorian year to Ethiopian date
        ethiopian_date = EthiopianDateConverter.to_ethiopian(year, 1, 1)
        
        # Debug info (can be removed in production)
        logger.debug(f"Ethiopian date type: {type(ethiopian_date)}, value: {ethiopian_date}")
        
        # Handle different return types
        if hasattr(ethiopian_date, 'year'):
            # Case 1: Returns a date object (most common in newer versions)
            # Original logic: [0] + 1 -> date.year + 1
            return ethiopian_date.year + 1
            
        elif isinstance(ethiopian_date, (tuple, list)) and len(ethiopian_date) >= 1:
            # Case 2: Returns a tuple/list (year, month, day)
            # Original logic exactly: [0] + 1
            return ethiopian_date[0] + 1
            
        else:
            # Case 3: Unexpected return type
            logger.warning(
                f"Unexpected return type from EthiopianDateConverter: "
                f"{type(ethiopian_date).__name__}. Using fallback calculation."
            )
            # Ethiopian year is roughly 7-8 years behind Gregorian
            # +1 offset handled by -7 instead of -8
            return year - 7
            
    except AttributeError as e:
        logger.error(f"AttributeError in Ethiopian date conversion: {e}")
        return year - 7
        
    except TypeError as e:
        logger.error(f"TypeError in Ethiopian date conversion: {e}")
        # Try alternative calling method
        try:
            # Some versions might expect a date object
            ethiopian_date = EthiopianDateConverter.to_ethiopian(date(year, 1, 1))
            if hasattr(ethiopian_date, 'year'):
                return ethiopian_date.year + 1
            return year - 7
        except Exception:
            return year - 7
            
    except Exception as e:
        logger.exception(f"Unexpected error converting year {year} to Ethiopian: {e}")
        return year - 7


@lru_cache(maxsize=128)
def ethiopian_year_to_gregorian(ethiopian_year: int) -> int:
    """
    Convert an Ethiopian year to the corresponding Gregorian year.
    
    Original logic: EthiopianDateConverter.to_gregorian(year, 1, 1).year - 1
    
    This is the inverse operation of gregorian_year_to_ethiopian.
    
    Examples:
        >>> ethiopian_year_to_gregorian(2016)
        2023  # Exact value depends on the library
    
    Args:
        ethiopian_year: Ethiopian year (e.g., 2016)
    
    Returns:
        Gregorian year
    
    Raises:
        ValueError: If ethiopian_year is invalid
    """
    # Input validation
    if not isinstance(ethiopian_year, int):
        raise ValueError(f"Year must be an integer, got {type(ethiopian_year).__name__}")
    
    try:
        # Convert Meskerem 1 (Ethiopian New Year) to Gregorian
        gregorian_date = EthiopianDateConverter.to_gregorian(ethiopian_year, 1, 1)
        
        # Handle different return types
        if hasattr(gregorian_date, 'year'):
            # Case 1: Returns a date object
            # Original logic: .year - 1
            return gregorian_date.year - 1
            
        elif isinstance(gregorian_date, (tuple, list)) and len(gregorian_date) >= 1:
            # Case 2: Returns a tuple/list
            return gregorian_date[0] - 1
            
        else:
            # Case 3: Unexpected return type
            logger.warning(
                f"Unexpected return type from EthiopianDateConverter: "
                f"{type(gregorian_date).__name__}. Using fallback calculation."
            )
            # Gregorian year is roughly 7-8 years ahead
            # -1 offset handled by +7 instead of +8
            return ethiopian_year + 7
            
    except Exception as e:
        logger.error(f"Error converting Ethiopian year {ethiopian_year} to Gregorian: {e}")
        return ethiopian_year + 7


def get_current_ethiopian_year() -> int:
    """
    Get the current Ethiopian year based on today's date.
    
    Returns:
        Current Ethiopian year
    """
    today = datetime.now()
    return gregorian_year_to_ethiopian(today.year)


def get_amharic_month(month: int) -> str:
    """
    Get the Amharic name for an Ethiopian month.
    
    Args:
        month: Ethiopian month number (1-12)
        
    Returns:
        Amharic month name
        
    Raises:
        IndexError: If month is not between 1 and 12
    """
    ethiopian_months = [
        "መስከረም",  # Meskerem
        "ጥቅምት",    # Tikimt
        "ኅዳር",      # Hidar
        "ታህሳስ",     # Tahsas
        "ጥር",       # Tir
        "የካቲት",    # Yekatit
        "መጋቢት",    # Megabit
        "ሚያዝያ",    # Miazia
        "ግንቦት",    # Ginbot
        "ሰኔ",       # Sene
        "ሐምሌ",      # Hamle
        "ነሐሴ",      # Nehase
    ]
    
    if not 1 <= month <= 12:
        raise IndexError(f"Month must be between 1 and 12, got {month}")
    
    return ethiopian_months[month - 1]


# ============================================================================
# Table data structures for reports
# ============================================================================

TableData = Union[Dict[str, "TableData"], List[List[Any]]]
"""
This data format is meant to be produced by functions in views.py because it's
kinda ergonomic to build simply by doing something like itertools.groupby() or
the bucket() function in views.py

Here is sample data in TableData format:
>>> table_data = {
  "first row, first col": {
    "first row, second col": [
      [
        "first row",
        "third col"
      ],
      [
        "second row",
        "third col"
      ]
    ],
    "third row, second col": [
      [
        "third row",
        "third col"
      ]
    ]
  },
  "fourth row, first col": [
    "fourth row, second col",
    "fourth row, third col"
  ]
}
"""

IndexedTableData = Dict[Tuple[int, int], Optional[Tuple[str, int]]]
"""
This data format is meant to be a precursor to actually rendering the table into
an HTML table, or an Excel workbook. 

Here is the same data used to demonstrate TableData above.
    >>> from pprint import pprint
    >>> pprint(generate_indexed_table_data(table_data))
    ({(0, 0): ('first row, first col', 2),
      (0, 1): ('first row, second col', 1),
      (0, 2): ('first row', 1),
      (0, 3): ('third col', 1),
      (1, 0): None,
      (1, 1): ('third row, second col', 1),
      (1, 2): ('third row', 1),
      (1, 3): ('third col', 1),
      (2, 0): ('fourth row, first col', 1),
      (2, 1): ('fourth row, second col', 1),
      (2, 2): ('fourth row, third col', 1)},
     3)

Each key is a zero-based, (row_no, col_no) index. Each value
is a tuple of the data of that cell and the rowspan of that cell, or
it will be None. A None value signifies no cell (for e.g., a <td>)
element should be "drawn" at that coordinate because a previous row
spanning multiple cells has taken up the cell.
"""


def generate_indexed_table_data(
    table_data: TableData, 
    row_offset: int = 0, 
    col_offset: int = 0
) -> Tuple[IndexedTableData, int]:
    """
    Generate indexed table data for rendering tables with merged cells.
    
    This function transforms a nested dictionary/list structure into a
    flat indexed representation suitable for HTML/Excel rendering.
    
    Args:
        table_data: Hierarchical table data structure
        row_offset: Starting row index
        col_offset: Starting column index
        
    Returns:
        Tuple of (indexed_data, total_rows_generated)
    """
    data_and_spans: IndexedTableData = {}
    rows_generated = _generate_indexed_table_data(
        table_data, data_and_spans, row_offset, col_offset
    )
    return data_and_spans, rows_generated


def _generate_indexed_table_data(
    table_data: TableData,
    data_and_spans: Dict[Tuple[int, int], Optional[Tuple[str, int]]],
    row_offset: int = 0,
    col_offset: int = 0,
) -> int:
    """
    Recursively populate data_and_spans with rowspan and cell data.
    
    Args:
        table_data: Current node in the table data structure
        data_and_spans: Dictionary to populate with cell data
        row_offset: Current row offset
        col_offset: Current column offset
        
    Returns:
        Number of rows generated from this node
    """
    if isinstance(table_data, list):
        if not table_data:
            return 0
            
        if isinstance(table_data[0], list):
            # Handle list of lists (multiple rows)
            for nested_data in table_data:
                if not isinstance(nested_data, list):
                    raise ValueError(f"Expected list, got {type(nested_data)}")
                row_offset += _generate_indexed_table_data(
                    nested_data, data_and_spans, row_offset, col_offset
                )
        else:
            # Handle flat list (single row)
            for col_num, nested_data in enumerate(table_data):
                if isinstance(nested_data, list):
                    raise ValueError(f"Expected non-list, got list at column {col_num}")
                actual_col = col_num + col_offset
                data_and_spans[(row_offset, actual_col)] = (str(nested_data), 1)
        return 1
        
    else:  # Dictionary
        total_num_generated_rows = 0
        for key, nested_data in table_data.items():
            num_generated_rows = _generate_indexed_table_data(
                nested_data, data_and_spans, row_offset, col_offset + 1
            )
            
            # Add the key cell with appropriate rowspan
            data_and_spans[(row_offset, col_offset)] = (str(key), num_generated_rows)
            
            # Mark cells covered by rowspan as None
            for i in range(1, num_generated_rows):
                data_and_spans[(row_offset + i, col_offset)] = None
                
            row_offset += num_generated_rows
            total_num_generated_rows += num_generated_rows
            
        return total_num_generated_rows


# ============================================================================
# HTMX helpers
# ============================================================================

def htmx_redirect(request, url: str = None):
    """
    Redirect properly for both HTMX and regular requests.
    
    Args:
        request: HTTP request object
        url: URL to redirect to (defaults to HTTP_REFERER)
        
    Returns:
        Appropriate redirect response
    """
    if url is None:
        url = request.META.get("HTTP_REFERER", "/")
    
    if not getattr(request, "htmx", False):
        return redirect(url)
    
    response = HttpResponseClientRedirect(url)
    response = retarget(response, "body")
    return response


# ============================================================================
# Dictionary utilities
# ============================================================================

def remove_empty(dictionary: Dict) -> Dict:
    """
    Remove items with falsy values from a dictionary.
    
    Args:
        dictionary: Input dictionary
        
    Returns:
        New dictionary with only truthy values
    """
    return {k: v for k, v in dictionary.items() if v}