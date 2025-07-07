import os


def get_data_path(data_type: str, country: str, filename: str) -> str:
    """
    Returns the full path to a data file relative to the current working directory.

    Args:
        data_type (str): 'raw' or 'processed'
        country (str): e.g. 'poland'
        filename (str): e.g. '2025_presidential_round2.csv'

    Returns:
        str: full path to the file
    """
    return os.path.join(os.getcwd(), "data", data_type, country.lower(), filename)
