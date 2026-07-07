# analytics/selectors/__init__.py
# Re-exports both selectors as a unified package.
# The old analytics/selectors.py is superseded by this package (Python gives
# priority to directories over .py files of the same name).

from analytics.selectors.dashboard import DashboardAnalyticsSelector
from analytics.selectors.comparative import ComparativeAnalyticsSelector

__all__ = [
    "DashboardAnalyticsSelector",
    "ComparativeAnalyticsSelector",
]
