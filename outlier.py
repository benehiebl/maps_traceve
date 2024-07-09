"""

Outlier detection algorithms + outlier removal

detection:
- zscore
- iqr
- isolation forest

"""


import pandas as pd
import numpy as np
import xarray as xr

from functools import partial
from collections import defaultdict

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler

from dataclasses import dataclass
from typing import Optional


def zscore(data, window=120, thresh=1):
    """
    Zscore finds outliers within a rolling window by using the average and standard deviation of the data within the window
    
    """

    d = pd.Series(data)
    roll = d.rolling(window=window, min_periods=1, center=True)
    
    avg = roll.mean()
    std = roll.std(ddof=0)
    z = d.sub(avg).div(std)   

    return ~z.between(-thresh, thresh), avg



def iqr(data, window=120, quantiles=[0.25,0.75], factor=1.5):

    d = pd.Series(data)
    roll = d.rolling(window=window, min_periods=1, center=True)

    q1 = roll.quantile(quantiles[0])
    q3 = roll.quantile(quantiles[1])
    iqr = q3 - q1

    return (data<q1-factor*iqr) | (data>q3+factor*iqr), roll.mean()


def iso_forest(data, contamination=0.005, n_trees=100, n_jobs=-1):

    data_nan = data[~np.isnan(data)].reshape(-1,1)
    model = IsolationForest(contamination=contamination, n_estimators=n_trees, n_jobs=n_jobs)
    model.fit(data_nan)

    out_nan = model.predict(data_nan)
    
    out = np.full(len(data), np.nan)
    out[~np.isnan(data)] = out_nan 


    return np.where(np.isnan(out) | (out == 1), False, True), None

@dataclass
class IsolationTree:
    X: np.ndarray
    indices: np.ndarray
    max_depth: int
    #left: Optional[IsolationTree] = None
    #right: Optional[IsolationTree] = None
    split_feature: int = None
    split_value: float = None

    def __post_init__(self):
        if self.X.shape[0] <= 1 or self.max_depth <= 0:
            return
        
        self.split_feature = np.random.randint(self.X.shape[1])
        self.split_value = np.random.uniform(self.X[:, self.split_feature].min(), self.X[:, self.split_feature].max())

        left_indices = self.X[:, self.split_feature] < self.split_value
        right_indices = self.X[:, self.split_feature] >= self.split_value

        self.left = IsolationTree(self.X[left_indices], self.indices[left_indices], self.max_depth - 1)
        self.right = IsolationTree(self.X[right_indices], self.indices[right_indices], self.max_depth - 1)
    
    def path_lengths(self):
        if self.left is None and self.right is None:
            return {idx: 1 for idx in self.indices}
        
        left_path_lengths = self.left.path_lengths()
        right_path_lengths = self.right.path_lengths()
        path_lengths = {**left_path_lengths, **right_path_lengths}
        return {idx: path_lengths[idx] + 1 for idx in self.indices}

def iso_forest_for_ts(X_in: np.ndarray, window=5, n_trees=100, max_depth=10, sample_frac=0.5, thresh=[-0.75,0.75]) -> np.ndarray:
    
    X = X_in[~np.isnan(X_in)]

    windows = np.lib.stride_tricks.sliding_window_view(X, window, axis=0)
    
    path_lengths_sum = defaultdict(int)
    path_lengths_counts = defaultdict(int)
    for _ in range(n_trees):
        data_sample = np.random.choice(windows.shape[0], int(windows.shape[0] * sample_frac))
        tree = IsolationTree(windows[data_sample], data_sample, max_depth)
        path_lengths = tree.path_lengths()
        for idx, path_length in path_lengths.items():
            path_lengths_sum[idx] += path_length
            path_lengths_counts[idx] += 1
    anomaly_scores = np.array([path_lengths_sum[idx] / path_lengths_counts[idx] for idx in range(windows.shape[0])])
    rec_anomaly = np.reciprocal(anomaly_scores)
    
    scaled_anomaly = MinMaxScaler().fit_transform(rec_anomaly.reshape(-1, 1)).flatten()
    scaled_anomaly = np.flip(np.insert(scaled_anomaly, 0, np.full(window//2, np.nan)))
    scaled_anomaly = np.flip(np.insert(scaled_anomaly, 0, np.full(window//2, np.nan)))
    out_anomaly = np.where((scaled_anomaly <= thresh[0]) | (scaled_anomaly >= thresh[1]), True, False)

    out = np.full(len(X_in), np.nan)
    out[~np.isnan(X_in)] = out_anomaly

    return out, scaled_anomaly


def outlier(data, mode= "drop", detection_mode="zscore", kwargs={}):
    """
    Wrapper aroudn outlier detection functions:
    detection modes: "zscore", "iqr", "iso_forest"
    modes: "drop", "avg"

    Parameter
    ---------
    data:   np.array
            1-D input array 
    mode:   str
    detetction_mode:    str
    kwargs:     dict
                kwargs for detection mode, see detection functions

    Returns
    -------
    np.array with replaced outliers
    """


    #import ts_utils.outlier 
    #out_det = getattr(ts_utils.outlier, detection_mode)
    out_det = globals()[detection_mode]
    out, avg = out_det(data, **kwargs)

    if mode =="drop":
        return np.where(out, np.nan, data)
    elif mode == "avg":
        return np.where(out, avg, data)
    


def xr_outlier(in_dataarray: xr.DataArray, mode="drop", detection_mode="zscore", window=60, kwargs={}, axis=0, inplace=True):
    """
    Wrapper to apply outlier detection to multidimensional xr.DataArray

    Parameters
    ----------
    see function outlier
    inplace:    bool
                if True in_dataarray will be modified directly, if False function returns new array with replaced outliers
    """


    if inplace == True:
        in_dataarray.data = np.apply_along_axis(partial(outlier, 
                                                    mode=mode, 
                                                    detection_mode=detection_mode, 
                                                    kwargs=kwargs),
                                             axis, 
                                             in_dataarray.values)
        
    elif inplace == False:
        dataarray = in_dataarray.copy()
        dataarray.data = np.apply_along_axis(partial(outlier, 
                                                    mode=mode, 
                                                    detection_mode=detection_mode, 
                                                    kwargs=kwargs),
                                             axis, 
                                             in_dataarray.values)

        return dataarray
