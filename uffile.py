import struct
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
        record_size = struct.unpack('>h', buf[padding+2:padding+4])[0] * 2
        bytes_read = len(buf) - padding
        bytes_to_read = record_size - bytes_read
        self._buf = buf[-bytes_read:] + f.read(bytes_to_read)

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

        data = raw_data / float(field_header['scale_factor'])
        mask = raw_data == self.mandatory_header['missing_data_value']
        data = np.ma.masked_array(data, mask)
        return data


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
