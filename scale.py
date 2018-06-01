# -*- coding: latin_1 -*-

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import csv 
import sys,imp,os,time,msvcrt
import argparse
from itertools import compress
import xml.etree.ElementTree as ET
import string
from ctypes import *
import re

### import DLL
the_DLL = CDLL("Rvea0284nc-64") #This is therefore expected to be in the current execution path

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
    latitude = float(arg_results.Latitude)
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
        lines = filter(lambda x: x.strip(), lines)
        
        data["meta"] = lines[0]
        printable = set(string.printable)
        data["meta"] = filter(lambda x: x in printable, data["meta"])
        
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

################# ATLAS CLASS DEFINITION FROM WASP USED FOR EXTRAPOLATION WITH DLL

class class_atlas:

    def __init__(self):
    
        c_float_roughness_lengths = c_float * 5
        self.__standard_roughness = c_float_roughness_lengths()
    
        c_float_heights = c_float * 5
        self.__standard_height = c_float_heights()
    
        c_float_weibullA = ((c_float * 36)* 5)* 5
        self.__weibull_A = c_float_weibullA()
       
        c_float_weibullK = ((c_float * 36)* 5)* 5
        self.__weibull_K = c_float_weibullK()
       
        c_float_frequency = (c_float * 36)* 5
        self.__frequency = c_float_frequency()
    
        self.__number_of_standard_heights = c_int()
        self.__number_of_standard_roughnesses = c_int()
    
        c_float_parameters = c_float * 80
        self.__param = c_float_parameters() 
    
    
    def loadfromdata(self, data):
        # nz0, nz, idd
        self.__data = dict(data)
        self.__meta = data["meta"]
        self.__number_of_standard_roughnesses = c_int(int(data["dim"][0]))
        self.__number_of_standard_heights = c_int(int(data["dim"][1]))
        self.__ns = c_int(int(data["dim"][2]))
        # z0st
        for i in range(0, self.__number_of_standard_roughnesses.value):
            self.__standard_roughness[i] = float(data["R"][i])
        # zst
        for i in range(0, self.__number_of_standard_heights.value):
            self.__standard_height[i] = float(data["H"][i])
    
        for i in range(0, self.__number_of_standard_roughnesses.value):
            for k in range(0, self.__ns.value):
                self.__frequency[i][k] = float(data["f"][i][k])
            for j in range(0, self.__number_of_standard_heights.value):	
                for k in range(0, self.__ns.value):                                                                             
                    self.__weibull_A[i][j][k] = float(data["A"][j+i*self.__number_of_standard_heights.value][k])
                    self.__weibull_K[i][j][k] = float(data["k"][j+i*self.__number_of_standard_heights.value][k])
    
    
    def resultsToData(self):#
        self.__data["dim"][0] = np.squeeze(np.ctypeslib.as_array(self.__number_of_standard_roughnesses,shape=(1,1)))
        self.__data["dim"][1] = np.squeeze(np.ctypeslib.as_array(self.__number_of_standard_heights,shape=(1,1)))
        self.__data["dim"][2] = np.squeeze(np.ctypeslib.as_array(self.__ns,shape=(1,1)))
        
        self.__data["R"] = np.squeeze(np.ctypeslib.as_array(self.__standard_roughness))
        self.__data["H"] = np.squeeze(np.ctypeslib.as_array(self.__standard_height))
        
        self.__data["f"] = np.squeeze(np.ctypeslib.as_array(self.__frequency))
        self.__data["A"] = np.squeeze(np.ctypeslib.as_array(self.__weibull_A)).reshape(25,36)
        self.__data["k"] = np.squeeze(np.ctypeslib.as_array(self.__weibull_K)).reshape(25,36)
        return self.__data

    def printResults(self):
        print("\n")
        print('z0st: [' + ',  '.join("%6.4f" % val for val in self.__standard_roughness) + ']')
        print('zst: [' + ',  '.join("%2.0f" % val for val in self.__standard_height) + ']')
        print(("count of sectors: %5i\n" % self.__ns.value))
        for iz0 in range(0, len(self.__standard_roughness)):
            print(("\n------ roughness type: %3i ------" % (iz0+1)))
            for iz in range(0, len(self.__standard_height)):
                if (iz == 0):
                    print('sector frequencies: \n [' + ', '.join("%8.5f" % val for val in self.__frequency[iz0][0:self.__ns.value]) + ']')
                print(("Weibul (A, K) of height type: %3i" % (iz+1)))
                print('[' + ', '.join("%8.5f" % val for val in self.__weibull_A[iz0][iz][0:self.__ns.value]) + ']')
                print('[' + ', '.join("%8.5f" % val for val in self.__weibull_K[iz0][iz][0:self.__ns.value]) + ']')
                    
    
    def __getpar(self):    
       xnoval = c_float() 
       buff = (c_char * 180) * 80 
       desc = buff()
       #Get the default configuration 
       the_DLL.deconf(self.__param, desc, byref(xnoval))
       #desc8 = desc[7].value.strip().decode() 
                                 	
    def extrapolate(self, new_roughness, latitude):
        
        direction_offset = c_float(0.0) #This must be set to zero.
    
        #As with the roughness, one of the height classes is used for the extrapolation. For simplicity, use the first.
        source_height_class = c_int(1)
    
        #The extrapolation is done from one roughness class. This variable specifies the index of the class to use.
        source_roughness_class_index = c_int(self.__number_of_standard_roughnesses.value) 
    
        #If there are < 5 classes, then a new class can be added and used to receive the extrapolation results
        #If there are already 5 classes, then the data in the fifth class is overwritten with the extrapolation results
        extrapolated_roughness_class_index = c_int(min(5, self.__number_of_standard_roughnesses.value + 1)) 
    
        #Make a call to retrieve the default parameter values for the calculation. No need to change these if you are using legacy LIB files.
        self.__getpar()            
    
        #Most of the arguments to this complex call are 'pure' inputs (the byref is necessary for other reasons)
        #But the results of the calculation are written to some of the initialised input arguments (as outputs)
        #Only the following arguments may or will change when you have invoked the method:
            #z0st (will have the new extrapolated roughness length, either in nz0+1 or in 5
            #nz0 (may be incremented if it is less than five as input
            #weibull_A, weibull_K, frequency
        the_DLL.CHANGEZ0ST_NC(byref(source_roughness_class_index), byref(extrapolated_roughness_class_index), byref(source_height_class), 
                              byref(c_float(latitude)), byref(c_float(new_roughness)), self.__standard_roughness, self.__standard_height, 
                              byref(self.__number_of_standard_roughnesses), byref(self.__number_of_standard_heights), 
                              self.__weibull_A, self.__weibull_K, self.__frequency, byref(self.__ns), 
                              byref(direction_offset), self.__param)
################# END ATLAS CLASS DEFINITION FROM WASP

def extrapolate_gwc(data, latitude):
    ### drive ATLAS CLASS 
    my_atlas = class_atlas()
    my_atlas.loadfromdata(data)
    my_atlas.extrapolate(1.5, latitude)
    expol_data = my_atlas.resultsToData()
    #my_atlas.printResults()
    
    return expol_data

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
        - A [# sectors]
        - k [# sectors]
        - f [# sectors]
        """
        output = ""
        output += '<WindAtlasWeibullWindRose RoughnessLengthNumber="%d" RoughnessLength="%.3f" ReferenceHeightNumber="%d" ReferenceHeight="%.1f" FormatVersion="1.0" CountOfSectors="%d">\n' \
                                             %(RoughnessLengthNumber,   RoughnessLength,        ReferenceHeightNumber,     ReferenceHeight,                            CountOfSectors)

        #if ((len(f)+len(A)+len(k))/3 != CountOfSectors):
            #print "Error: Count of sectors does not correspond to length of A, k, and f data."
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
        for r in range(data["dim"][0]): 
            for h in range(data["dim"][1]):
                f.write(writeWindRose(r+1, data["R"][r], h+1, data["H"][h], data["sect"], data["f"][r], data["A"][r*data["dim"][1]+h], data["k"][r*data["dim"][1]+h]))
        f.write(closing)                                                                
        f.close() 
        
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
    print ("Note: You selected extrapolation of the gwc. This feature is not yet tested.\n")
    data_scaled_exp = extrapolate_gwc(data_scaled, latitude)
    export_gwc(data_scaled_exp, ofile + "_exp")
    print "The extrapolated GWC is %s.gwc.\n" % (ofile + "_exp")

print "\n############### End Scale LIB ###############\n"


# end




