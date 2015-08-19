import struct
import datetime

import numpy as np


class UFFile(object):
    """
    A class for reading data from Universal Format (UF) files.

    """

    def __init__(self, filename):
        """ initialize. """
        self._filename = filename

        f = open(filename, 'rb')
        buf = f.read(8)

        if buf[:2] == 'UF':
            padding = 0
        elif buf[2:4] == 'UF':
            padding = 2
        elif buf[4:6] == 'UF':
            padding = 4
        else:
            raise IOError('file in not a valid UF file')
        self.padding = padding

        # read in the first record
        self.rays = []
        while len(buf) == 8:
            record_size = struct.unpack('>h', buf[padding+2:padding+4])[0] * 2
            bytes_read = len(buf) - padding
            bytes_to_read = record_size - bytes_read
            record = buf[-bytes_read:] + f.read(bytes_to_read)
            self.rays.append(UFRay(record))
            f.read(padding)
            buf = f.read(8)

        # determine sweep information
        self.ray_sweep_numbers = self._get_ray_sweep_numbers()
        self.nsweeps = len(np.unique(self.ray_sweep_numbers))
        first_ray_in_sweep, last_ray_in_sweep = self._get_sweep_limits()
        self.first_ray_in_sweep = first_ray_in_sweep
        self.last_ray_in_sweep = last_ray_in_sweep

        f.close()

    def _get_ray_sweep_numbers(self):
        nrays = len(self.rays)
        ray_sweep_numbers = np.empty((nrays, ), dtype='int32')
        for i, ray in enumerate(self.rays):
            ray_sweep_numbers[i] = ray.mandatory_header['sweep_number']
        return ray_sweep_numbers

    def _get_sweep_limits(self):

        first_ray_in_sweep = np.empty(self.nsweeps, dtype='int32')
        last_ray_in_sweep = np.empty(self.nsweeps, dtype='int32')
        unique_sweep_numbers = np.unique(self.ray_sweep_numbers)
        for i, sweep_number in enumerate(unique_sweep_numbers):
            matches = np.where(self.ray_sweep_numbers == sweep_number)
            first_ray_in_sweep[i] = matches[0][0]
            last_ray_in_sweep[i] = matches[0][-1]
        return first_ray_in_sweep, last_ray_in_sweep

    def get_field_data(self, field_number):

        first_ray = self.rays[0]
        ngates = len(first_ray.all_data[field_number])
        nrays = len(self.rays)
        missing_data_value = first_ray.mandatory_header['missing_data_value']
        scale_factor = first_ray.field_headers[field_number]['scale_factor']

        raw_data = np.empty((nrays, ngates), 'int16')
        for i, ray in enumerate(self.rays):
            ray_data = ray.all_data[field_number]
            bins = len(ray_data)
            raw_data[i, :bins] = ray.all_data[field_number]
            raw_data[i, bins:] = missing_data_value

        data = raw_data / float(scale_factor)
        mask = raw_data == missing_data_value
        return np.ma.masked_array(data, mask)

    def get_azimuths(self):
        nrays = len(self.rays)
        azimuth = np.empty((nrays, ), dtype='float32')
        for i, ray in enumerate(self.rays):
            azimuth[i] = ray.mandatory_header['azimuth'] / 64.
        return azimuth

    def get_elevations(self):
        nrays = len(self.rays)
        elevation = np.empty((nrays, ), dtype='float32')
        for i, ray in enumerate(self.rays):
            elevation[i] = ray.mandatory_header['elevation'] / 64.
        return elevation

    def get_sweep_fixed_angles(self):
        fixed = np.empty((self.nsweeps, ), dtype='float32')
        for i, ray_num in enumerate(self.first_ray_in_sweep):
            fixed[i] = self.rays[ray_num].mandatory_header['fixed_angle'] / 64.
        return fixed


class UFRay(object):
    """
    A class for reading data from a UF Ray (Record)
    """

    def __init__(self, record):

        self._buf = record

        # read in the mandatory header
        self.mandatory_header = _unpack_from_buf(
            self._buf, 0, UF_MANDATORY_HEADER)

        # read in optional header (if present)
        if self.mandatory_header['offset_optional_header'] != 0:
            offset = (self.mandatory_header['offset_optional_header'] - 1) * 2
            self.optional_header = _unpack_from_buf(
                self._buf, offset, UF_OPTIONAL_HEADER)
        else:
            self.optional_header = None

        # read in data header
        offset = (self.mandatory_header['offset_data_header'] - 1) * 2
        self.data_header = _unpack_from_buf(self._buf, offset, UF_DATA_HEADER)
        # read in field position information
        self.field_data = [
            _unpack_from_buf(self._buf, offset + 6 + i*4, UF_FIELD_POSITION)
            for i in range(self.data_header['record_nfields'])]

        # read field data
        self.field_headers = []
        self.all_data = [self.get_field_data(i) for i in
                         range(self.data_header['record_nfields'])]

        return

    def get_field_data(self, field_number):

        offset = (self.field_data[field_number]['offset_field_header'] - 1) * 2
        field_header = _unpack_from_buf(self._buf, offset, UF_FIELD_HEADER)
        self.field_headers.append(field_header)

        offset = (field_header['data_offset'] - 1) * 2
        s = self._buf[offset:offset+field_header['nbins']*2]
        raw_data = np.fromstring(s, dtype='>i2')

        return raw_data

    def get_datetime(self):
        year = self.mandatory_header['year']
        if year < 1900:
            year += 2000   # years after 2000, 11 -> 2011
        month = self.mandatory_header['month']
        day = self.mandatory_header['day']
        hour = self.mandatory_header['hour']
        minute = self.mandatory_header['minute']
        second = self.mandatory_header['second']
        return datetime.datetime(year, month, day, hour, minute, second)


def _structure_size(structure):
    """ Find the size of a structure in bytes. """
    return struct.calcsize('>' + ''.join([i[1] for i in structure]))


def _unpack_from_file(fh, structure):
    """ Unpack a structure from an open file object. """
    size = _structure_size(structure)
    string = fh.read(size)
    return _unpack_structure(string, structure)


def _unpack_from_buf(buf, pos, structure):
    """ Unpack a structure from a buffer. """
    size = _structure_size(structure)
    return _unpack_structure(buf[pos:pos + size], structure)


def _unpack_structure(string, structure):
    """ Unpack a structure from a string """
    fmt = '>' + ''.join([i[1] for i in structure])  # UF is big-endian
    lst = struct.unpack(fmt, string)
    return dict(zip([i[0] for i in structure], lst))


# UF structures
# From Appendix C


# Formats of stucture elements
INT16 = 'h'


# C.3 UF Mandatory header
UF_MANDATORY_HEADER = (
    ('uf_string', '2s'),
    ('record_length', INT16),
    ('offset_optional_header', INT16),
    ('offset_local_use_header', INT16),
    ('offset_data_header', INT16),
    ('record_number', INT16),
    ('volume_number', INT16),
    ('ray_number', INT16),
    ('ray_record_number', INT16),
    ('sweep_number', INT16),
    ('radar_name', '8s'),
    ('site_name', '8s'),
    ('latitude_degrees', INT16),
    ('latitude_minutes', INT16),
    ('latitude_seconds', INT16),
    ('longitude_degrees', INT16),
    ('longitude_minutes', INT16),
    ('longitude_seconds', INT16),
    ('height_above_sea_level', INT16),
    ('year', INT16),
    ('month', INT16),
    ('day', INT16),
    ('hour', INT16),
    ('minute', INT16),
    ('second', INT16),
    ('time_zone', '2s'),
    ('azimuth', INT16),
    ('elevation', INT16),
    ('sweep_mode', INT16),
    ('fixed_angle', INT16),
    ('sweep_rate', INT16),
    ('generation_year', INT16),
    ('generation_month', INT16),
    ('generation_day', INT16),
    ('generation_facility_name', '8s'),
    ('missing_data_value', INT16),
)

UF_OPTIONAL_HEADER = (
    ('project_name', '8s'),
    ('baseline_azimuth', INT16),
    ('baseline_elevation', INT16),
    ('volume_hour', INT16),
    ('volume_minute', INT16),
    ('volume_second', INT16),
    ('tape_name', '8s'),
    ('flag', INT16)
)

UF_DATA_HEADER = (
    ('ray_nfields', INT16),
    ('ray_nrecords', INT16),
    ('record_nfields', INT16),
)

UF_FIELD_POSITION = (
    ('data_type', '2s'),
    ('offset_field_header', INT16),
)

UF_FIELD_HEADER = (
    ('data_offset', INT16),
    ('scale_factor', INT16),
    ('range_start_km', INT16),
    ('range_start_m', INT16),
    ('range_spacing_m', INT16),
    ('nbins', INT16),
    ('pulse_width_m', INT16),
    ('beam_width_h', INT16),    # degrees * 64
    ('beam_width_v', INT16),    # degrees * 64
    ('bandwidth', INT16),       # Reciever bandwidth in MHz * 16
    ('polarization', INT16),     # 1: hort, 2: vert 3: circular, 4: ellip
    ('wavelength_cm', INT16),   # cm * 64
    ('sample_size', INT16),
    ('threshold_data', '2s'),
    ('threshold_value', INT16),
    ('scale', INT16),
    ('edit_code', '2s'),
    ('prt_ms', INT16),
    ('bits_per_bin', INT16),    # Miust be 16
)

UF_FSI_VEL = (
    ('nyquist', INT16),
    ('spare', INT16),
)

UF_FSI_DM = (
    ('radar_constant', INT16),
    ('noise_power', INT16),
    ('reciever_gain', INT16),
    ('peak_power', INT16),
    ('antenna_gain', INT16),
    ('pulse_duration', INT16),
)
