from osgeo import gdal
import rasterio

# format = "GTiff"
#
# driver = gdal.GetDriverByName( format )
# metadata = driver.GetMetadata()
#
# # if gdal.DCAP_CREATE in metadata and metadata[gdal.DCAP_CREATE] == 'YES':
# #      print ('Driver %s supports Create() method.' % format)
# # if gdal.DCAP_CREATECOPY in metadata and metadata[gdal.DCAP_CREATECOPY] == 'YES':
# #     print ('Driver %s supports CreateCopy() method.' % format)
# driver = gdal.GetDriverByName('GTiff')
# dst_filename = '/tmp/x_tmp.tif'
# dst_ds = driver.Create(dst_filename, 512, 512, 1, gdal.GDT_Byte)
import netCDF4
from netCDF4 import Dataset

data = Dataset("/home/admin/klimaschiff/data/CMAQv5.2_Benchmark_SingleDay_Input_09_12_2017/SE52BENCH/single_day/cctm_input/emis/gridded_area/emis_mole_all_20110701_cb6_bench.nc")
data.dimensions["COL"]



import numpy as np
from rasterio.transform import Affine

x = np.linspace(792000, 80*12000+792000, 12000)
y = range(-1080000, 80*12000 + -1080000, 12000)
X, Y = np.meshgrid(x, y)
Z = (data.variables["SO2"][0,:])[0]



res = (x[-1] - x[0]) / 12000
transform = Affine.translation(x[0] - res / 2, y[0] - res / 2) * Affine.scale(res, res)
transform
new_dataset = rasterio.open(
    'test.tif',
    'w',
    driver='GTiff',
    height=Z.shape[0],
    width=Z.shape[1],
    count=1,
    dtype=Z.dtype,
    crs='EPSG:25832',
    transform=transform)

new_dataset.write(Z, 1)
new_dataset.close()

test = rasterio.open('test.tif')
# get raster cell
test.index(792963.29,-1077297.99)
# get value of raster cell
test.read(1)[34,12]

from pyproj import Proj, transform

inProj = Proj(init='epsg:25832')
outProj = Proj(init='epsg:4326')
x1,y1 = 792963.29,-1077297.99
x2,y2 = transform(inProj,outProj,y1, x1)
print(x2,y2)
