"""
L2_FINAL_NDVI.py uses ArcPy and Python 2.7
Boyd Shearer, April 2014, for University of Kentucky GEO 409, Advanced GIS
Purpose of script is to create Kentucky State Park trail maps using state and federal data.
Script will convert any workspaces containing vector and raster data to Kentucky Single Zone FIPS 1600 CRS and clip to an extent defining an area of interest.
Elevation rasters from http://viewer.nationalmap.gov/basic with a .img entension will make DEM elevation rasters and a HillShade_3d
Aerial photographs (NAIP 2012) from http://earthexplorer.usgs.gov/ will be mosiac into a single raster and a NDVI will be created.
State park vector data was downloaded from http://kygisserver.ky.gov/geoportal/catalog/main/home.page
Vector trail layer will have a new field created and evaluate a label for placement in QGIS
"""
import arcpy
import arcpy.sa

arcpy.env.overwriteOutput = True

#Set directory for input feature class layers
fcworkspace = 'T:/users/BoydsGIS/GEO409/L02/downloaded-data/fc/'

#Set directory for input raster layers
rasterworkspace = 'T:/users/BoydsGIS/GEO409/L02/downloaded-data/rasters/'

#Set directory for output raster layers
published_data = "T:/users/BoydsGIS/GEO409/L02/published/"

#Set output GDB that will contain our built vector layers
gdbworkspace = 'T:/users/BoydsGIS/GEO409/L02/workspace.gdb/'

#Set Ky Trails Layer for attributes modification
fc = 'T:/users/BoydsGIS/GEO409/L02/workspace.gdb/KY_Trails'

#Set our extent, which was given to us by the client. Also contains our final CRS
extent = "T:/users/BoydsGIS/GEO409/L02/extent/AreaOfInterest.shp"

#Create our SpatialReference object that we will use to define other output CRS
sr = arcpy.SpatialReference(r'T:\users\BoydsGIS\GEO409\L02\extent\AreaOfInterest.prj')

################# Vector Layers Project and Clip ################# 

#Set current workspace to feature class folder
arcpy.env.workspace = fcworkspace 

fclist = arcpy.ListFeatureClasses() 

#Iterate alphabetically through our list and declare each feature classes fc
for fc in fclist:
	
	desc = arcpy.Describe(fc)
	crs = desc.SpatialReference  
    #Show info to user
	print "\n{0} is projected in {1} with code {2}".format(desc.name,crs.name,crs.factoryCode)
	#Define temporary and final output layer names
	tempfc = gdbworkspace + "temp"
	outfc = gdbworkspace + desc.basename.replace(" ","_")
	print outfc
	#Project function
	arcpy.Project_management (fc, tempfc, sr)
	#Clip function
	arcpy.Clip_analysis (tempfc, extent, outfc)
	#Delete function
	arcpy.Delete_management(tempfc)

################# Raster Layers Project and Clip ################# 

#Set current workspace to raster folder
arcpy.env.workspace = rasterworkspace

#Get list of rasters
rlist = arcpy.ListRasters() 

for raster in rlist:
	desc = arcpy.Describe(raster) #create Describe object 
	crs = desc.SpatialReference #Get spatial reference system for rasters
	#Print information about raster
	print "{0} is in the CRS: {1} with code: {2}\n".format(desc.basename,crs.name,crs.factoryCode)
	#If raster doesn't have a CRS, then stop, but if it does then project and clip into our CRS
	if crs.name == "Unknown":
		break
	else:
		tempraster = gdbworkspace + "temp"
		outraster = gdbworkspace + desc.basename[:12].replace(" ","_") #replace function to remove spaces from name
		print outraster +" is being projected and clipped..."
		arcpy.ProjectRaster_management(raster, tempraster, sr, "CUBIC" )
		arcpy.Clip_management (tempraster, "#", outraster, extent, "#", "ClippingGeometry")
		arcpy.Delete_management(tempraster)

################# Mosaic NAIP raster to published folder################# 

#Create mosaiced raster from mulitple images
arcpy.env.workspace = gdbworkspace
mosaicraster = ""

rlist = arcpy.ListRasters() 
print rlist
for raster in rlist:
	desc = arcpy.Describe(raster)
	if desc.basename[0:2] == "m_":
		mosaicraster = mosaicraster + desc.basename[:12] + ";"
print mosaicraster
arcpy.MosaicToNewRaster_management (mosaicraster, gdbworkspace, "NAIP2014", "#", "#", "#", 4)
arcpy.CopyRaster_management ("NAIP2014", published_data+"NAIP_2014.tif")

rlist = arcpy.ListRasters() 
for raster in rlist:
	desc = arcpy.Describe(raster)
	if desc.basename[0:2] == "m_":
		arcpy.Delete_management(raster)
	else:
		print "all good yo!"

################# Modify trail attributes ################# 

#Inspect attributes for Ky Trails and create label field to use for final map
#Build list of fields and print them

fields = arcpy.ListFields(fc)
for field in fields:
    print("{0} is a type of {1} with a length of {2}".format(field.name, field.type, field.length))

#Iterate through records and look at field values
fields = ['TRAIL_NAME','GIS_MILE']
cursor = arcpy.da.SearchCursor(fc,fields)
for row in cursor:
	print "{0} is {1} miles long.".format(row[0], row[1])

#Add a new field called 'Label' and calculate a string to use for our map label
arcpy.AddField_management (fc, "Label", "TEXT", "#", "#", 50)
fields = ['TRAIL_NAME','GIS_MILE', 'Label']
cursor = arcpy.da.UpdateCursor(fc,fields)
for row in cursor:
	#print "{0}, {1} mi".format(row[0],round(row[1],2))
	if row[1] > 0.2:
		row[2] = row[0] + " Trail " + str(round(row[1],2)) +" mi"
	else:
		row[2] = ""
	cursor.updateRow(row)
	print row[2]
del cursor, row

################# Create hillshade and elevation rasters for use in QGIS ################# 

#Check out extensions
arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")

arcpy.env.workspace = gdbworkspace

#convert img to TIFFs with elevation raster in feet and hillshade 
elev = arcpy.ListRasters("img*")
for raster in elev:
	rasterObject = arcpy.Describe(raster)
	name = rasterObject.basename 
	elevFeet = published_data + "elevation_feet.tif"
	hillshade = published_data + "elevation_hillshade.tif"
	r1 = arcpy.sa.Raster(raster)*3.281
	r1.save(elevFeet)
	arcpy.HillShade_3d(elevFeet, hillshade, 270, 55)

################# EXTRA: Create NDVI and canopy layer ################# 

#Create NDVI (extra stuff)
naip = arcpy.ListRasters("NAIP*")
for raster in naip:
	rasterObject = arcpy.Describe(raster)
	name = rasterObject.basename
	print name
	RedBand = published_data + rasterObject.basename +"_1.tif"
	NIRBand = published_data + rasterObject.basename +"_4.tif"
	compRed = rasterObject.catalogPath + "/Band_1"
	print "Extracting Near Infrared Band to {0}".format(RedBand)
	arcpy.CompositeBands_management(compRed,RedBand)
	compNIR = rasterObject.catalogPath + "/Band_4"
	print "Extracting Near Infrared Band ato {0}".format(NIRBand)
	arcpy.CompositeBands_management(compNIR,NIRBand)
	ndvi = rasterObject.basename + "_ndvi.tif"
	print "Creating NDVI as {0} ... to: ".format(ndvi)
	rastermath=(arcpy.sa.Raster(NIRBand)-arcpy.sa.Raster(RedBand))/arcpy.sa.Float(arcpy.sa.Raster(NIRBand)+arcpy.sa.Raster(RedBand))
	print published_data+ndvi
	rastermath.save(published_data+ndvi)
	arcpy.Delete_management(RedBand)
	arcpy.Delete_management(NIRBand)

arcpy.env.workspace = published_data
ndvi = arcpy.ListRasters("*ndvi.*")
for raster in ndvi:
	print raster
	rasterObject = arcpy.Describe(raster)
	rasterLayer = arcpy.sa.Raster(raster)
	ndvi = published_data + "canopy.tif"
	print "Makin vegetation layer with NDVI value greater {0}".format(ndvi)
	r2 = rasterLayer > 0.2
	r2.save(ndvi)

arcpy.CheckInExtension("Spatial")
arcpy.CheckInExtension("3D")

################# Export vector layers to published shapefiles ################# 

#Set workspace
arcpy.env.workspace = gdbworkspace 

#Create list object of all Feature Classes in our workspace
fclist = arcpy.ListFeatureClasses() 

#Iterate alphabetically through our list and declare each feature classes fc
for fc in fclist:
    
	#Create Describe object with properties: http://pro.arcgis.com/en/pro-app/arcpy/functions/describe.htm
	desc = arcpy.Describe(fc)
	arcpy.FeatureClassToFeatureClass_conversion (fc, published_data, desc.basename + ".shp")

