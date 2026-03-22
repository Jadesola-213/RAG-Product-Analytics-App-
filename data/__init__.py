from .ingestion import load_data
from .cleaning import clean_data
from .features import engineer_features


def build_dataframe(data_dir=None) -> "pd.DataFrame":
    """Full pipeline: load → clean → feature-engineer."""
    import pandas as pd
    from config import DATA_DIR
    directory = data_dir or DATA_DIR
    raw = load_data(directory)
    cleaned = clean_data(raw)
    return engineer_features(cleaned)
