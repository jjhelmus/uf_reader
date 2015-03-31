
import struct


def read_uf(filename):
    f = open(filename, 'rb')
    buf = f.read(6)
    
    if buf[:2] == 'UF':
        f.seek(0)
        extra_offset = 0
    elif buf[2:4] == 'UF':
        f.seek(2)
        extra_offset = 2
    elif buf[4:6] == 'UF':
        f.seek(4)
        extra_offset = 4
    else:
        raise IOError('file in not a valid UF file')

    mandatory_header = read_header_block(f)
    dic = {'mandatory_header': mandatory_header}

    offset_optional_header = mandatory_header['offset_optional_header']
    offset_local_use_header = mandatory_header['offset_local_use_header']
    offset_data_header = mandatory_header['offset_data_header']
    
    if offset_optional_header != offset_local_use_header:
        f.seek(2 * (offset_optional_header - 1) + extra_offset)
        optional_header = read_optional_header_block(f)
        dic['optional_header'] = optional_header
    
    if offset_local_use_header != offset_data_header:
        pass    # do not know structure of local use header

    

    return dic



def read_header_block(f):
    fmt = '>2s 9h 8s 8s 13h 2s 8h 8s h'
    l = struct.unpack(fmt, f.read(struct.calcsize(fmt)))

    d = {}
    d['uf_string'] = l[0]                   # 2s
    d['record_length'] = l[1]               # 9h:1
    d['offset_optional_header'] = l[2]      # 9h:2
    d['offset_local_use_header'] = l[3]     # 9h:3
    d['offset_data_header'] = l[4]          # 9h:4
    d['physical_record_number'] = l[5]      # 9h:5
    d['volume_scan_number'] = l[6]          # 9h:6
    d['ray_number'] = l[7]                  # 9h:7
    d['ray_record_number'] = l[8]           # 9h:8
    d['sweep_number'] = l[9]                # 9h:9
    d['radar_name'] = l[10]                 # 8s
    d['site_name'] = l[11]                  # 8s
    d['latitude_degrees'] = l[12]           # 13h:1
    d['latitude_minutes'] = l[13]           # 13h:2
    d['latitude_seconds'] = l[14]           # 13h:3
    d['longitude_degrees'] = l[15]          # 13h:4
    d['longitude_minutes'] = l[16]          # 13h:5
    d['longitude_seconds'] = l[17]          # 13h:6
    d['height_above_sea_level'] = l[18]     # 13h:7
    d['year'] = l[19]                       # 13h:8
    d['month'] = l[20]                      # 13h:9
    d['day'] = l[21]                        # 13h:10
    d['hour'] = l[22]                       # 13h:11
    d['minute'] = l[23]                     # 13h:12
    d['second'] = l[24]                     # 13h:13
    d['time_zone'] = l[25]                  # 2s
    d['azimuth'] = l[26]                    # 8h:1
    d['elevation'] = l[27]                  # 8h:2
    d['sweep_mode'] = l[28]                 # 8h:3
    d['fixed_angle'] = l[29]                # 8h:4
    d['sweep_rate'] = l[30]                 # 8h:5
    d['generation_year'] = l[31]            # 8h:6
    d['generation_month'] = l[32]           # 8h:7
    d['generation_day' ] = l[33]            # 8h:8
    d['generation_facility_name'] = l[34]   # 8s
    d['missing_data_value'] = l[35]          # h
    
    return d


def read_optional_header_block(f):
    fmt = '>8s 5h 8s h'
    l = struct.unpack(fmt, f.read(struct.calcsize(fmt)))
    d = {}
    d['project_name'] = l[0]            # 8s
    d['baseline_azimuth'] = l[1]        # 5h:1
    d['baseline_elevation'] = l[2]      # 5h:2
    d['volume_start_hour'] = l[3]       # 5h:3
    d['volume_start_minute'] = l[4]     # 5h:4
    d['volume_start_second'] = l[5]     # 5h:5
    d['field_tape_name'] = l[6]         # 8s
    d['spacing_flag'] = l[7]            # h
    return d


def read_data_header(f):
    fmt = '>3h'
    l = struct.unpack(fmt, f.read(struct.calcsize(fmt)))
    d = {}
    d['number_ray_fields'] = l[0]
    d['number_ray_records'] = l[1]
    d['number_record_fields'] = l[2]
    nfields = l[0]
    d['field_name'] = ['XX'] * nfields
    d['offset_field_header'] = [0] * nfields
    for i in range(nfields):
        fmt = '>2s h'
        l = struct.unpack(fmt, f.read(struct.calcsize(fmt)))
        d['field_name'][i] = l[0]
        d['offset_field_header'][i] = l[1]
    return d

def read_field_header(f):
    fmt = '>13h 2s 2h 2s 2h'
    l = struct.unpack(fmt, f.read(struct.calcsize(fmt)))
    d = {}
    d['data_position'] = l[0]           # 13h:1
    d['scale_factor'] = l[1]            # 13h:2
    d['start_range'] = l[2]             # 13h:3
    d['range_adjustment'] = l[3]        # 13h:4
    d['volume_spacing'] = l[4]          # 13h:5
    d['number_volumes'] = l[5]          # 13h:6
    d['volume_depth'] = l[6]            # 13h:7
    d['beam_width_horizontal'] = l[7]   # 13h:8
    d['beam_width_vertical'] = l[8]     # 13h:9
    d['reciever_bandwidth'] = l[9]      # 13h:10
    d['polarization'] = l[10]           # 13h:11
    d['wavelength'] = l[11]             # 13h:12
    d['number_of_samples'] = l[12]      # 13h:13
    d['threshold_field'] = l[13]        # 2s
    d['threshold_value'] = l[14]        # 2h:1
    d['scale'] = l[15]                  # 2h:2
    d['edit_code'] = l[16]
    d['pulse_repetition_time'] = l[17]
    d['bits_per_volume'] = l[18]
    return d
