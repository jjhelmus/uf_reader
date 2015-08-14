
import pyart
import uf

radar =  uf.read_uf('sample_files/test.uf')
ref_radar = pyart.io.read_rsl('sample_files/test.uf')


def test_time():
    assert ref_radar.time['units'] == radar.time['units']
    assert np.allclose(ref_radar.time['data'], radar.time['data'])
