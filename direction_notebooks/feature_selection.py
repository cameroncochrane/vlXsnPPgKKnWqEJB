import pandas as pd
import numpy as np

from sklearn.feature_selection import mutual_info_classif

def eta_squared(categories: pd.Series, values: pd.Series) -> float:
    """
    Calculate eta-squared for a categorical target and numeric feature.

    Example:
    >>> features = list(X.columns)
    >>> eta_results_5 = pd.Series(
    >>>    {
    >>>        feature: eta_squared(
    >>>            X_y_5['Direction_5'],
    >>>            X_y_5[feature],
    >>>        )
    >>>        for feature in features
    >>>   },
    >>>    name="eta_squared",
    >>> ).sort_values(ascending=False)

    >>> print(eta_results_5)
    
    """

    categories = pd.Series(categories)
    values = pd.Series(values)

    valid = categories.notna() & values.notna()
    categories = categories.loc[valid]
    values = values.loc[valid]

    if values.empty:
        return np.nan

    overall_mean = values.mean()

    ss_between = 0.0

    for category in categories.unique():
        group = values.loc[categories == category]

        ss_between += len(group) * (
            group.mean() - overall_mean
        ) ** 2

    ss_total = ((values - overall_mean) ** 2).sum()

    if ss_total == 0:
        return 0.0

    return ss_between / ss_total