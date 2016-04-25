"""
make_canopy.py uses ArcPy, Python 2.7
Boyd Shearer, April 2014, for University of Kentucky GEO 409, Advanced GIS

This script creates an approximate NDVI and canopy rasters from a Landsat 8 scene. This script uses raw digital numbers and doesn't perform any radiometric correction.  
Notes: Putting Landsat 8’s Bands to Work, https://www.mapbox.com/blog/putting-landsat-8-bands-to-work/

"""
import arcpy
import arcpy.sa
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

######## Set input directory for a single scene of Landsat 8 imagery ########
rasterworkspace = r'S:\Arcdata\BoydsGIS\zWork\Landsat_8_NDVI\LC81160342013259LGN00'

######## Set output NDVI layer ########
final_ndvi = r'S:\Arcdata\BoydsGIS\zWork\Landsat_8_NDVI\workspace.gdb\ndvi'

######## Set output canopy layer assuming an NDVI > 0.2 ########
final_canopy = r'S:\Arcdata\BoydsGIS\zWork\Landsat_8_NDVI\workspace.gdb\canopy'


print """#------------ Creating NDVI and canopy rasters ------------#"""

arcpy.env.workspace = rasterworkspace

# Extract and load the near-infrared band
b5 = arcpy.ListRasters("*_B5*")
for r in b5:
	dr = arcpy.Describe(r)
	print "Extracting near infrared band from {0}".format(dr.name)
	band5 = arcpy.sa.Raster(dr.catalogPath)

# Extract and load the red band
b4 = arcpy.ListRasters("*_B4*")
for r in b4:
	dr = arcpy.Describe(r)
	print "Extracting red band from {0}".format(dr.name)
	band4 = arcpy.sa.Raster(dr.catalogPath) 

#Calculate the NDVI raster
print "Making NDVI"
ndvi = (band5-band4)/arcpy.sa.Float(band5+band4) #Make ouput of division a float number
ndvi.save(final_ndvi)

#Calculate the canopy raster assuming an NDVI > 0.2 
print "Making Canopy layer with NDVI > 0.2"
canopy = ndvi > 0.2
canopy.save(final_canopy)

arcpy.CheckInExtension("Spatial")

print "#------------ All good, Yo! ------------#"
