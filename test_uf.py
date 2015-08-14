
import pyart
import uf

import numpy as np

radar =  uf.read_uf('sample_files/test.uf')
ref_radar = pyart.io.read_rsl('sample_files/test.uf')


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
    assert np.allclose(ref_radar.sweep_mode['data'], radar.sweep_mode['data'])

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
    assert np.allclose(ref_radar.fields[field]['data'],
                       radar.fields[field]['data'])
