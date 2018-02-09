import numpy as np
import csv 
import sys,imp,os,time,msvcrt
import argparse

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
ifile = arg_results.ifile[:-4] # removes .lib extension
percentage = float(arg_results.percentage)

if AutoParentName:
    ofile = '{}_{:.0f}'.format(ifile,percentage)

### functions

def __now__():                    
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def scale_lib(ifile, ofile, percentage):
    return 0

def export_gwc(ifile, ofile):
    return 0

def extrapolate_gwc(ifile, ofile, latitude):
    return 0

### main program

scale_lib(ifile, ofile, percentage)

export_gwc(ifile, ofile)

if b_latitude:
    extrapolate_gwc(ifile, ofile, latitude)

# end




