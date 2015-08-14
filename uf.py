
import struct

import datetime
import warnings

import numpy as np

from pyart.config import FileMetadata, get_fillvalue
from pyart.io.common import make_time_unit_str, _test_arguments, dms_to_d
from pyart.core.radar import Radar
from uffile import UFFile


UF_SWEEP_MODES = {
    0: 'calibration',
    1: 'ppi',
    2: 'coplane',
    3: 'rhi',
    4: 'vpt',
    5: 'target',
    6: 'manual',
    7: 'idle',
}

def read_uf(filename, field_names=None, additional_metadata=None,
               file_field_names=False, exclude_fields=None,
               valid_range_from_file=True, units_from_file=True, **kwargs):
    """
    Read a UF File.

    Parameters
    ----------
    filename : str
        Name of Universal format file to read data from.
    field_names : dict, optional
        Dictionary mapping field names in the file names to radar field names.
        Unlike other read functions, fields not in this dictionary or having a
        value of None are still included in the radar.fields dictionary, to
        exclude them use the `exclude_fields` parameter. Fields which are
        mapped by this dictionary will be renamed from key to value.
    additional_metadata : dict of dicts, optional
        This parameter is not used, it is included for uniformity.
    file_field_names : bool, optional
        True to force the use of the field names from the file in which
        case the `field_names` parameter is ignored. False will use to
        `field_names` parameter to rename fields.
    exclude_fields : list or None, optional
        List of fields to exclude from the radar object. This is applied
        after the `file_field_names` and `field_names` parameters.
    valid_range_from_file : bool, optional
        True to extract valid range (valid_min and valid_max) for all
        field from the file when they are present.  False will not extract
        these parameters.
    units_from_file : bool, optional
        True to extract the units for all fields from the file when available.
        False will not extract units using the default units for the fields.

    Returns
    -------
    radar : Radar
        Radar object.

    """
    # test for non empty kwargs
    _test_arguments(kwargs)

    # create metadata retrieval object
    filemetadata = FileMetadata('uf', field_names, additional_metadata,
                                file_field_names, exclude_fields)

    # Open UF file and get handle
    ufile = UFFile(filename)
    nsweeps = ufile.mandatory_header['sweep_number']

    # time
    year = ufile.mandatory_header['year']
    if year < 1900:
        year += 2000   # years after 2000, 11 -> 2011
    month = ufile.mandatory_header['month']
    day = ufile.mandatory_header['day']
    hour = ufile.mandatory_header['hour']
    minute = ufile.mandatory_header['minute']
    second = ufile.mandatory_header['second']
    start_time = datetime.datetime(year, month, day, hour, minute, second)
    time = filemetadata('time')
    time['units'] = make_time_unit_str(start_time)
    time['data'] = np.array([0], dtype='float64')

    # range
    _range = filemetadata('range')
    ngates = ufile.field_header['nbins']
    start = ufile.field_header['range_start_m']
    step = ufile.field_header['range_spacing_m']
    # this gives distances to the start of each gate, add step/2 for center
    _range['data'] = np.arange(ngates, dtype='float32') * step + start
    _range['meters_to_center_of_first_gate'] = start
    _range['meters_between_gates'] = step

    # latitude, longitude and altitude
    latitude = filemetadata('latitude')
    longitude = filemetadata('longitude')
    altitude = filemetadata('altitude')
    lat_deg = ufile.mandatory_header['latitude_degrees']
    lat_min = ufile.mandatory_header['latitude_minutes']
    lat_sec = ufile.mandatory_header['latitude_seconds'] / 64.
    lat = dms_to_d([lat_deg, lat_min, lat_sec])
    lon_deg = ufile.mandatory_header['longitude_degrees']
    lon_min = ufile.mandatory_header['longitude_minutes']
    lon_sec = ufile.mandatory_header['longitude_seconds'] / 64.
    lon = dms_to_d([lon_deg, lon_min, lon_sec])
    latitude['data'] = np.array([lat], dtype='float64')
    longitude['data'] = np.array([lon], dtype='float64')
    altitude['data'] = np.array(
        [ufile.mandatory_header['height_above_sea_level']], dtype='float64')

    # metadata
    metadata = filemetadata('metadata')
    metadata['original_container'] = 'UF'
    metadata['site_name'] = ufile.mandatory_header['site_name']
    metadata['radar_name'] = ufile.mandatory_header['radar_name']

    # sweep_start_ray_index, sweep_end_ray_index
    sweep_start_ray_index = filemetadata('sweep_start_ray_index')
    sweep_end_ray_index = filemetadata('sweep_end_ray_index')
    #sweep_start_ray_index['data'] = gfile.start_ray.astype('int32')
    #sweep_end_ray_index['data'] = gfile.end_ray.astype('int32')

    # sweep number
    sweep_number = filemetadata('sweep_number')
    sweep_number['data'] = np.arange(nsweeps, dtype='int32')
    #try:
        #sweep_number['data'] = gfile.what_attrs('set_idx', 'int32')
    #except KeyError:
        #sweep_number['data'] = np.arange(gfile.nsweeps, dtype='int32')

    # sweep_type
    scan_type = UF_SWEEP_MODES[ufile.mandatory_header['sweep_mode']]
    #scan_type = gfile.raw_scan0_group_attr('what', 'scan_type').lower()
    # check that all scans in the volume are the same type
    #if not gfile.is_file_single_scan_type():
        #raise NotImplementedError('Mixed scan_type volume.')
    #if scan_type not in ['ppi', 'rhi']:
        #message = "Unknown scan type: %s, reading as RHI scans." % (scan_type)
        #warnings.warn(message)
        #scan_type = 'rhi'

    # sweep_mode, fixed_angle
    sweep_mode = filemetadata('sweep_mode')
    fixed_angle = filemetadata('fixed_angle')
    #if scan_type == 'rhi':
        #sweep_mode['data'] = np.array(gfile.nsweeps * ['rhi'])
        #fixed_angle['data'] = gfile.how_attrs('azimuth', 'float32')
    #elif scan_type == 'ppi':
        #sweep_mode['data'] = np.array(gfile.nsweeps * ['azimuth_surveillance'])
        #fixed_angle['data'] = gfile.how_attrs('elevation', 'float32')



    # elevation
    elevation = filemetadata('elevation')
    #start_angle = gfile.ray_header('elevation_start', 'float32')
    #stop_angle = gfile.ray_header('elevation_stop', 'float32')
    #elevation['data'] = _avg_radial_angles(start_angle, stop_angle)

    # azimuth
    azimuth = filemetadata('azimuth')
    #start_angle = gfile.ray_header('azimuth_start', 'float32')
    #stop_angle = gfile.ray_header('azimuth_stop', 'float32')
    #azimuth['data'] = _avg_radial_angles(start_angle, stop_angle) % 360.

    # fields
    fields = {}

    # instrument_parameters
    instrument_parameters = None

    #ufile.close()

    return Radar(
        time, _range, fields, metadata, scan_type,
        latitude, longitude, altitude,
        sweep_number, sweep_mode, fixed_angle, sweep_start_ray_index,
        sweep_end_ray_index,
        azimuth, elevation,
        instrument_parameters=instrument_parameters)

