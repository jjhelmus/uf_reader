
import struct

import datetime
import warnings

import numpy as np

from pyart.config import FileMetadata, get_fillvalue
from pyart.io.common import make_time_unit_str, _test_arguments
from pyart.core.radar import Radar
from uffile import UFFile

def read_uf(filename, field_names=None, additional_metadata=None,
               file_field_names=False, exclude_fields=None,
               valid_range_from_file=True, units_from_file=True, **kwargs):
    """
    Read a UF File.

    Parameters
    ----------
    filename : str
        Name of GAMIC HDF5 file to read data from.
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

    # time
    time = filemetadata('time')
    year = ufile.mandatory_header['year']
    #t_data = gfile.ray_header('timestamp', 'int64')
    #start_epoch = t_data[0] // 1.e6     # truncate to second resolution
    #start_time = datetime.datetime.utcfromtimestamp(start_epoch)
    #time['units'] = make_time_unit_str(start_time)
    #time['data'] = ((t_data - start_epoch * 1.e6) / 1.e6).astype('float64')
    time['data'] = np.arange(100)

    # range
    _range = filemetadata('range')
    #ngates = int(gfile.raw_scan0_group_attr('how', 'bin_count'))
    #range_start = float(gfile.raw_scan0_group_attr('how', 'range_start'))
    #range_step = float(gfile.raw_scan0_group_attr('how', 'range_step'))
    # range_step may need to be scaled by range_samples
    # XXX This gives distances to start of gates not center, this matches
    # Radx but may be incorrect, add range_step / 2. for center
    _range['data'] = np.arange(100)
    #_range['data'] = (np.arange(ngates, dtype='float32') * range_step +
                      #range_start)
    #_range['meters_to_center_of_first_gate'] = range_start
    #_range['meters_between_gates'] = range_step

    # latitude, longitude and altitude
    latitude = filemetadata('latitude')
    longitude = filemetadata('longitude')
    altitude = filemetadata('altitude')
    #latitude['data'] = gfile.where_attr('lat', 'float64')
    #longitude['data'] = gfile.where_attr('lon', 'float64')
    #altitude['data'] = gfile.where_attr('height', 'float64')

    # metadata
    metadata = filemetadata('metadata')
    metadata['original_container'] = 'UF'

    # sweep_start_ray_index, sweep_end_ray_index
    sweep_start_ray_index = filemetadata('sweep_start_ray_index')
    sweep_end_ray_index = filemetadata('sweep_end_ray_index')
    #sweep_start_ray_index['data'] = gfile.start_ray.astype('int32')
    #sweep_end_ray_index['data'] = gfile.end_ray.astype('int32')

    # sweep number
    sweep_number = filemetadata('sweep_number')
    sweep_number['data'] = np.array([0])
    #try:
        #sweep_number['data'] = gfile.what_attrs('set_idx', 'int32')
    #except KeyError:
        #sweep_number['data'] = np.arange(gfile.nsweeps, dtype='int32')

    # sweep_type
    scan_type = 'ppi'
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
        instrument_parameters=instrument_parameters,
        ray_angle_res=None, rays_are_indexed=None, scan_rate=None,
        target_scan_rate=None)

