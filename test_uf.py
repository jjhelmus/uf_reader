import StringIO

import pyart
import uf
import uffile

import numpy as np
from numpy.testing import assert_raises

radar = uf.read_uf('sample_files/test.uf')
ref_radar = pyart.io.read_rsl('sample_files/test.uf', file_field_names=True)


def test_time():
    assert ref_radar.time['units'] == radar.time['units']
    assert np.allclose(ref_radar.time['data'], radar.time['data'])


def test_range():
    assert np.allclose(ref_radar.range['data'], radar.range['data'])
    assert (ref_radar.range['meters_to_center_of_first_gate'] ==
            radar.range['meters_to_center_of_first_gate'])
    assert (ref_radar.range['meters_between_gates'] ==
            radar.range['meters_between_gates'])


def test_lat_lon_alt():
    assert np.allclose(ref_radar.latitude['data'], radar.latitude['data'])
    assert np.allclose(ref_radar.longitude['data'], radar.longitude['data'])
    assert np.allclose(ref_radar.altitude['data'], radar.altitude['data'])


def test_sweep_start_ray_index():
    assert np.allclose(ref_radar.sweep_start_ray_index['data'],
                       radar.sweep_start_ray_index['data'])


def test_sweep_end_ray_index():
    assert np.allclose(ref_radar.sweep_end_ray_index['data'],
                       radar.sweep_end_ray_index['data'])


def test_sweep_number():
    assert np.allclose(ref_radar.sweep_number['data'],
                       radar.sweep_number['data'])


def test_scan_type():
    assert radar.scan_type == ref_radar.scan_type


def test_sweep_mode():
    assert ref_radar.sweep_mode['data'] == radar.sweep_mode['data']


def test_fixed_angle():
    assert np.allclose(ref_radar.fixed_angle['data'],
                       radar.fixed_angle['data'])


def test_elevation():
    assert np.allclose(ref_radar.elevation['data'], radar.elevation['data'])


def test_azimuth():
    assert np.allclose(ref_radar.azimuth['data'], radar.azimuth['data'])


def test_fields():
    for field in ref_radar.fields.keys():
        yield check_field, field


def check_field(field):
    assert np.ma.allclose(ref_radar.fields[field]['data'],
                          radar.fields[field]['data'], atol=0.005)
    mask1 = np.ma.getmaskarray(ref_radar.fields[field]['data'])
    mask2 = np.ma.getmaskarray(radar.fields[field]['data'])
    assert np.all(mask1 == mask2)


def test_raises():
    fake_bad_file = StringIO.StringIO('XXXXXXXX')
    assert_raises(IOError, uf.read_uf, fake_bad_file)


def test_read_fileobj():
    fh = open('sample_files/test.uf', 'rb')
    radar = uf.read_uf(fh)
    fh.close()


def test_instrument_parameters():
    assert radar.scan_rate is not None
    assert 'pulse_width' in radar.instrument_parameters
    assert 'radar_beam_width_h' in radar.instrument_parameters
    assert 'radar_beam_width_v' in radar.instrument_parameters
    assert 'radar_receiver_bandwidth' in radar.instrument_parameters
    assert 'polarization_mode' in radar.instrument_parameters
    assert 'frequency' in radar.instrument_parameters
    assert 'prt' in radar.instrument_parameters
    assert 'nyquist_velocity' in radar.instrument_parameters


def test_failures():
    ufile = uffile.UFFile('sample_files/test.uf')
    ufile.rays[0].field_headers[1].pop('nyquist')
    assert ufile.get_nyquists() is None

    ufile.rays[0].field_headers[0]['polarization'] = 99
    assert ufile.get_sweep_polarizations()[0] == 'elliptical'
