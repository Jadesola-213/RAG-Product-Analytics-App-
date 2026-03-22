"""
Module-level singletons populated once at startup.
All callback modules import from here.

  DF        : enriched orders DataFrame
  RETRIEVER : built RAGRetriever instance
"""

import pandas as pd

DF: pd.DataFrame = None          # type: ignore[assignment]
RETRIEVER = None                 # RAGRetriever
