import numpy as np
import csv 
import sys,imp,os,time,msvcrt
import argparse
from itertools import compress
import xml.etree.ElementTree as ET

### arg parser
parser = argparse.ArgumentParser(description='--- A Python UL DEWI program to scale libs and convert them to gwcs ---')

parser.add_argument('ifile', action='store',default=False,\
                    help="Name of the LIB-file with extension .lib.")

parser.add_argument('percentage', action='store',default=False,\
                    help="Percentage to scale the Lib. Value between [0..200]")

parser.add_argument('--OutputFilename','-o', action='store', dest='Ofile', default='AUTOPARENTNAME',\
                    help='Name of the Output file without filetype extension. Default value is "AUTOPARENTNAME" (e.g.: derived directly from input file and percentage), otherwise specify')

parser.add_argument('--Extrapolate','-e', action='store', dest='Latitude',\
                    help='Not implemented yet: Latitude of desired location in decimal degrees. Only used for extrapolation.')


arg_results, arg_errors = parser.parse_known_args()

###################### Arguments - Filename
if not arg_results.Ofile in ['AUTOPARENTNAME']:
    filename = arg_results.Ofile
    AutoParentName=False
elif arg_results.Ofile.lower() == 'autoparentname' :
    AutoParentName=True

###################### Arguments - Extrapolate
if arg_results.Latitude != None:
    latitude = arg_results.Latitude
    b_latitude = True
elif arg_results.Latitude == None :
    b_latitude = False

### variables
ifile = arg_results.ifile
ifile_short = arg_results.ifile[:-4] # removes .lib extension
percentage = float(arg_results.percentage)

if AutoParentName:
    ofile = '{}_{:04.0f}'.format(ifile_short,percentage*10)
else:
    ofile = filename
### functions

def __now__():                    
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def convert_to_np(data, row_length):
    """Converts 2D-lists to numpy array."""
    nparr = np.zeros([ len(data), row_length])
    for (line_count,line) in enumerate(data):
        temp_line = np.array(line.split())
        temp_line = temp_line.astype(float)             
        nparr[line_count] = temp_line
    return nparr
    
def open_lib(ifile):
    """Opens lib with name ifile and returns stationmeta, arraydim, rlengths, heights, sectors, data."""
    with open(ifile, 'rb') as f:
        lines = f.readlines()
        lines = [x.strip() for x in lines]
        data = {}

        data["meta"] = lines[0]
        data["dim"]  = np.array(lines[1].split()).astype(int)
        data["R"]    = np.array(lines[2].split()).astype(float)  #[m]
        data["H"]    = np.array(lines[3].split()).astype(float)  #[m]
        data["sect"] = int(data["dim"][2])
        
        data_block = lines[4:]

        # frequencies
        data["f"] = convert_to_np(data_block[::len(data["H"])*2+1],data["sect"]) 
        
        # create masks for A, k value
        mask = np.ones(len(data_block), dtype=bool)
        mask[::len(data["H"])*2+1] = False
                
        AK = convert_to_np(list(compress(data_block,mask)),data["sect"])
        
        data["A"] = AK[::2]
        data["k"] = AK[1::2]
        f.close() 
    return data

def write_lib(ofile,data):
    """Writes libfile to filename "ofile" using the dictionary data.
    Keys of data are:
    meta: metadata
    dim:  dimensions
    R:    roughness lengths
    H:    heights
    sect: nb. of sectors
    f:    frequencies
    A:    Weibull A
    k:    Weibull k"""
    with open(ofile+".lib",'wb') as f:
        f.write(data["meta"]+"\n")
        f.write("\t".join(map(str, data["dim"]))+"\n")
        f.write("\t".join('%.3f' %x for x in data["R"])+"\n")
        f.write("\t".join('%.1f' %x for x in data["H"])+"\n")
        for i in range(data["dim"][0]):
            f.write("\t".join(map(str, data["f"][i]))+"\n")
            for j in range(data["dim"][1]):
                f.write("\t".join('%.2f' %x for x in data["A"][i*data["dim"][1]+j])+"\n")
                f.write("\t".join('%.2f' %x for x in data["k"][i*data["dim"][1]+j])+"\n")
                #f.write(str(i*data["dim"][1]+j)+" A: "+"\t".join('%.2f' %x for x in data["A"][i*data["dim"][1]+j])+"\n")
                #f.write(str(i*data["dim"][1]+j)+" k: "+"\t".join('%.2f' %x for x in data["k"][i*data["dim"][1]+j])+"\n")
        f.close()
    
def scale_lib(ifile, ofile, percentage):
    data = open_lib(ifile)
    data["A"] = data["A"] * (percentage/100.0)**(1.0/3.0)
    write_lib(ofile,data)
    return data

def export_gwc(data, ofile):
    """Exports the data object to a .gwc file (XML) following the version number FormatVersion="01.01.0002"""
    # functions
    def writeWindRose(RoughnessLengthNumber, RoughnessLength, ReferenceHeightNumber, ReferenceHeight, CountOfSectors, f, A, k):
        """Writes <WindAtlasWeibullWindRose ... > ... </WindAtlasWeibullWindRose> to string.
        Needs as input:
        - RoughnessLengthNumber
        - RoughnessLength
        - ReferenceHeightNumber
        - ReferenceHeight
        - CountOfSectors
        - A [12 sectors]
        - k [12 sectors]
        - f [12 sectors]
        """
        output = ""
        output += '<WindAtlasWeibullWindRose RoughnessLengthNumber="%d" RoughnessLength="%.3f" ReferenceHeightNumber="%d" ReferenceHeight="%.1f" FormatVersion="1.0" CountOfSectors="%d">\n' \
                                             %(RoughnessLengthNumber,   RoughnessLength,        ReferenceHeightNumber,     ReferenceHeight,                            CountOfSectors)

        if ((len(f)+len(A)+len(k))/3 != CountOfSectors):
            print "Error: Count of sectors does not correspond to length of A, k, and f data."
        
        # WeibullWind entries
        SectorWidthDegrees = 360/CountOfSectors        
        
        for i in range(CountOfSectors):
            output += '<WeibullWind Index="%d" CentreAngleDegrees="%d" SectorWidthDegrees="%d" SectorFrequency="%.6E" WeibullA="%.3f" WeibullK="%.3f"/>\n' \
                    %(                   i+1,      i*SectorWidthDegrees, SectorWidthDegrees,                  f[i]/100.0,          A[i],     k[i])
                    
        output += '</WindAtlasWeibullWindRose>\n'
        
        return output
    
################# strings for file
    header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    
    provenance = """<Provenance>
    <ProfileModelParameters>
        <RveaConfiguration FormatVersion="02.00.0001">
            <RveaParameter ID="PROFILEMODEL" Value="Classic" IsDefault="1"/>
            <RveaParameter ID="FRACSTAC" Value="0.6" IsDefault="1"/>
            <RveaParameter ID="RMSINVSTA" Value="0.007" IsDefault="1"/>
            <RveaParameter ID="RMSINVUNSTA" Value="0.04" IsDefault="1"/>
            <RveaParameter ID="OFSLANDTA" Value="-40" IsDefault="1"/>
            <RveaParameter ID="EABLLAND" Value="400" IsDefault="1"/>
            <RveaParameter ID="FRACSTACWAT" Value="0.4" IsDefault="1"/>
            <RveaParameter ID="RMSINVSTASEA" Value="0.002" IsDefault="1"/>
            <RveaParameter ID="RMSINVUNSTASEA" Value="0.02" IsDefault="1"/>
            <RveaParameter ID="OFSWATERTA" Value="-8" IsDefault="1"/>
            <RveaParameter ID="EABLSEA" Value="333" IsDefault="1"/>
            <RveaParameter ID="LMTEABL" Value="0.5" IsDefault="1"/>
            <RveaParameter ID="STABFAC" Value="0.002" IsDefault="1"/>
            <RveaParameter ID="RMSLAND" Value="100" IsDefault="1"/>
            <RveaParameter ID="RMSWATER" Value="30" IsDefault="1"/>
            <RveaParameter ID="OFSLAND" Value="-40" IsDefault="1"/>
            <RveaParameter ID="OFSWATER" Value="-8" IsDefault="1"/>
            <RveaParameter ID="FACGEOH" Value="1" IsDefault="1"/>
            <RveaParameter ID="FACGEOSEA" Value="1" IsDefault="1"/>
            <RveaParameter ID="POWERLAW" Value="1.5" IsDefault="1"/>
        </RveaConfiguration>
    </ProfileModelParameters>
</Provenance>
"""
    closing = "</RveaGeneralisedMeanWindClimate>\n"
    
    meta = '<RveaGeneralisedMeanWindClimate FormatVersion="01.01.0002" LowestCompatibleFormatVersion="01.00.0000" SavingComponent="Rvea0182 version 1.14.0026" \
    Description="%s" CountOfSectors="%0.f" SectorOneCentreAngle="0" CountOfReferenceHeights="%0.f" CountOfReferenceRoughnessLengths="%0.f">\n' % \
        (data["meta"],        data["dim"][2],                                                data["dim"][1],                         data["dim"][0])
    
##### write to file
    with open(ofile+".gwc",'wb') as f:
        f.write(header)
        f.write(meta)
        f.write(provenance)
        for (r, rlength) in enumerate(data["R"]):
            for (h, height) in enumerate(data["H"]):
                f.write(writeWindRose(r+1, rlength, h+1, height, data["sect"], data["f"][r], data["A"][r*data["dim"][1]+h], data["k"][r*data["dim"][1]+h]))
        f.write(closing)                                                                
        f.close() 
        
    return 0

def extrapolate_gwc(ifile, ofile, latitude):
    return 0

######## main program: call above defined functions  ################
print "\n############### Scale LIB ###################\n"
print "Make sure used input LIB is properly formatted as no format checks are performed!\n"
print "Scales %s with %.2f%% into %s.lib and %s.gwc.\n" % (ifile, percentage, ofile, ofile)
data_scaled = scale_lib(ifile, ofile, percentage)

# normalize frequencies to 100
sums = np.sum(data_scaled["f"], axis=1)
for (i, su) in enumerate(sums):
    data_scaled["f"][i] = data_scaled["f"][i]*100.0/su

export_gwc(data_scaled, ofile)

           
if b_latitude:
    print ("Note: You selected extrapolation of the gwc. This feature is not yet implemented.")
    extrapolate_gwc(ifile, ofile, latitude)

print "\n############### End Scale LIB ###############\n"

# end




