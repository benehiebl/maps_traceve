"""

Smoothing algorithms for time series xarray data

Whittaker Smoothing:
    Eiler et al. 2003

Fast Fourier Transform Smoothing:
    see ATkinson et al. 2013

Radial Basis Function Kernel Smoothing:
    see Atkinson et al. 2013

    "Gaussian" kernel

"""

import numpy as np
import xarray as xr

import scipy.sparse as sparse
from scipy.sparse.linalg import splu
from scipy.ndimage import gaussian_filter1d
from whittaker_eilers import WhittakerSmoother

from functools import partial
import sys

def interpolate_na(data, kwargs={}):
    """
    linearly interpolate nans in data (no extrapolation) in one direction
    """

    if np.isnan(data).all():
        return data
    else:
        ok = ~np.isnan(data)
        xp = ok.ravel().nonzero()[0]
        fp = data[~np.isnan(data)]
        x  = np.isnan(data).ravel().nonzero()[0]

        # Replacing nan values
        out = data.copy()
        out[np.isnan(data)] = np.interp(x, xp, fp, **kwargs)
        return out


def whittaker_smooth_v1(data, lmbd=8**2, d = 1):
    """
    Implementation of the Whittaker smoothing algorithm,
    based on Eilers 2003
    
    The larger 'lmbd', the smoother the data.
    For smoothing of a complete data series with no NaNs and sampled at equal intervals
    
    Parameters:
    -----------
    data       : vector containing raw data
    lmbd    : parameter for the smoothing algorithm (roughness penalty)
    d       : order of the smoothing 

    Returns:
    --------
    vector of the smoothed data.
    """

    m = len(data)
    E = sparse.eye(m, format='csc')
    D = _speyediff(m, d, format='csc')
    coefmat = E + lmbd * D.conj().T.dot(D)
    z = splu(coefmat).solve(data)
    return z 

def _speyediff(N, d, format='csc'):
    """
    (utility function)
    Construct a d-th order sparse difference matrix based on 
    an initial N x N identity matrix
    
    Final matrix (N-d) x N
    """
    
    assert not (d < 0), "d must be non negative"
    shape = (N-d, N)
    diagonals = np.zeros(2*d + 1)
    diagonals[d] = 1.
    for i in range(d):
        diff = diagonals[:-1] - diagonals[1:]
        diagonals = diff
    offsets = np.arange(d+1)
    spmat = sparse.diags(diagonals, offsets, shape, format=format)
    return spmat


def whittaker_smooth(data, lmbd=8**2, d = 1):
    """
    Implementation of the Whittaker smoothing algorithm,
    based on Eilers 2003
    
    The larger 'lmbd', the smoother the data.
    For smoothing of a complete data series with no NaNs and sampled at equal intervals
    
    Parameters:
    -----------
    data       : vector containing raw data
    lmbd    : parameter for the smoothing algorithm (roughness penalty)
    d       : order of the smoothing 

    Returns:
    --------
    vector of the smoothed data.
    """

    x_input = np.arange(0, len(data)) 
    nans = np.isnan(data)
    weights = np.where(nans == True, 0.0, 1.0)
    d_nan = np.where(np.isnan(data), -99999, data)

    whittaker_smoother = WhittakerSmoother(
        lmbda=lmbd,
        order=d,
        data_length=len(data),
        x_input=x_input,
        weights=weights,
    )

    smoothed = whittaker_smoother.smooth(d_nan)

    return smoothed

    
def fourier_smooth(data, axis=0, n_harmonics=4, n_years=1, cutoff_frequency=None):
    """
    Smoothing via Fast Fourier Transform, selection of frequency harmonics and ifft.

    n_harmonics should be chosen according to the ideal value for 1 year. 
    n_hamornics will the be transformed internally to:
    n_hamornics_m = n_harmonics + 7*np.log(n_years)
    
    Implemented only for real data with no imaginary part.
    time series with no NaNS and equally spaced time intervalls.

    Parameters:
    -----------
    in_dataarray:   xr.DataArray
                    input array time series
    axis:           int
                    position of axis over which will be smoothed
    n_harmonics:    int
                    1 is sinus-like smoothing, higher numbers fit better towards raw data
    cutoff_frequency:   float
                    frequency where data should be cur off, not working as off now
    inplace:        bool
                    if False a copy of the smoothed data is returned, if True the input dataarrays data is replaced by the smoothed one, default: True

    Return
    ------
    if inplace is False: xr.DataArray
    """

    #n_harmonics = int(n_harmonics + 7*np.log(n_years))

    # apply fft for 1d or 2d data
    if len(data.shape) == 1:
        rft = np.fft.rfft(data)
        frequencies = np.fft.rfftfreq(len(data))
    else:
        rft = np.fft.rfftn(data, axes=(axis,))
        frequencies = np.fft.rfftfreq(len(data))

    # cut frequency or set unwanted harmonics to 0
    if cutoff_frequency != None:    
        rft[np.abs(frequencies) > cutoff_frequency] = 0
    else: 
        #rft[:n_harmonics[0]] = 0
        #rft[n_harmonics[1]:] = 0
        rft[n_harmonics:] = 0

    # perform inverse fft
    if len(data.shape) == 1:
        data_smooth = np.fft.irfft(rft, data.shape[0])#, axes=0)
    else:
        data_smooth = np.fft.irfftn(rft, s=(data.shape[axis],), axes=(axis,))
    
    return data_smooth



    
def rbf_smooth_v1(in_data, epsilon=12, rbf_func="gaussian"):

    #data = ((in_data - in_data.min()) / (in_data.max() - in_data.min())) * (20000 - 0) + 0
    
    x = np.arange(0, len(in_data))

    smoothed_cases = np.zeros(in_data.shape)
    for x_position in x:

        if rbf_func == "gaussian":
            k = np.exp(
                -((x - x_position) ** 2) / (2 * (epsilon ** 2))
            )

            k = k/(k.sum())
        smoothed_cases[x_position] = (in_data * k).sum()

    smoothed_cases = np.array(smoothed_cases)
    #s = ((smoothed_cases - smoothed_cases.min()) / (smoothed_cases.max() - smoothed_cases.min())) * (in_data.max() - in_data.min()) + in_data.min()

    return smoothed_cases

def rbf_smooth(in_data, epsilon=12, rbf_func="gaussian"):

    if rbf_func == "gaussian":
        smoothed_cases = gaussian_filter1d(in_data, epsilon)

    return smoothed_cases



def smoother(data, interpolate_nan=False, axis=0, smooth_mode="whittaker_smooth", kwargs={}):
    """
    Wrapper aroudn smoothing functions:
    smoothing modes: "fourier_smooth", "whittaker_smooth", "rbf_smooth"

    Parameter
    ---------
    data:   np.array
            1-D input array 
    smooth_mode:    str
    kwargs:     dict
                kwargs for smoothing mode, see smoothing functions

    Returns
    -------
    np.array with replaced outliers
    """
    if interpolate_nan:
        data = np.apply_along_axis(partial(interpolate_na), axis, data)

    if not smooth_mode.startswith("whittaker"):
        if np.isnan(data).any():
            sys.exit("smoother: data contains NaN. Please specify interpolate_na=True or remove NaNs manually.")

    #import ts_utils.smooth
    #s_mode = getattr(ts_utils.smooth, smooth_mode)
    s_mode = globals()[smooth_mode]
    return s_mode(data, **kwargs)



def xr_smooth(in_dataarray: xr.DataArray, interpolate_nan=False, smooth_mode="whittaker", kwargs={}, axis=0, inplace=True):
    """
    Wrapper to apply smoothing to multidimensional xr.DataArray

    Parameters
    ----------
    see function outlier
    inplace:    bool
                if True in_dataarray will be modified directly, if False function returns new array with replaced outliers
    """


    if inplace == True:
        in_dataarray.data = np.apply_along_axis(partial(smoother,  
                                                    interpolate_nan=interpolate_nan,
                                                    axis=0,
                                                    smooth_mode=smooth_mode, 
                                                    kwargs=kwargs),
                                             axis, 
                                             in_dataarray.values)
        
    elif inplace == False:
        dataarray = in_dataarray.copy()
        dataarray.data = np.apply_along_axis(partial(smoother, 
                                                    interpolate_nan=interpolate_nan,
                                                    axis=0,
                                                    smooth_mode=smooth_mode, 
                                                    kwargs=kwargs),
                                             axis, 
                                             in_dataarray.values)

        return dataarray   