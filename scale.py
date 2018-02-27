import numpy as np
import csv 
import sys,imp,os,time,msvcrt
import argparse
from itertools import compress

### arg parser
parser = argparse.ArgumentParser(description='--- A Python UL DEWI program to scale libs and convert them to gwcs ---')

parser.add_argument('ifile', action='store',default=False,\
                    help="Name of the LIB-file with extension .lib.")

parser.add_argument('percentage', action='store',default=False,\
                    help="Percentage to scale the Lib. Value between [0..200]")

parser.add_argument('--OutputFilename','-o', action='store', dest='Ofile', default='AUTOPARENTNAME',\
                    help='Name of the Output file without filetype extension. Default value is "AUTOPARENTNAME" (e.g.: derived directly from input file and percentage), otherwise specify')

parser.add_argument('--Extrapolate','-e', action='store', dest='Latitude',\
                    help='Latitude of desired location in decimal degrees.')


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
    ofile = '{}_{:.0f}'.format(ifile_short,percentage)

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
        
        data["A"]= AK[::2]
        data["k"]= AK[1::2]
        f.close() 
    return data

def scale_lib(ifile, ofile, percentage):
    data = open_lib(ifile)
    print data        
    return 0

def export_gwc(ifile, ofile):
    return 0

def extrapolate_gwc(ifile, ofile, latitude):
    return 0

### main program: call above defined functions

scale_lib(ifile, ofile, percentage)

export_gwc(ifile, ofile)

if b_latitude:
    extrapolate_gwc(ifile, ofile, latitude)

# end




