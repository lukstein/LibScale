This program does:
- scale WAsP Libs by an energy percentage x (v*x^(1/3))
- generate gwc from WASP
- not yet: extrapolate gwc if necessary

Usage: python scale.py [-h] [--OutputFilename OFILE] [--Extrapolate LATITUDE] ifile percentage

To display help: python scale.py -h

Example: python scale.py testlib.lib 110