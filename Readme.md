This program does:
- scale WAsP Libs by an energy percentage x (v*x^(1/3)) - enter percentage as 89 instead of 0.89 or 89%
- generate gwc
- with option "-e Latitude", it extrapolates to the roughness length of 1.5m

Example: python scale.py testlib.lib 110 [-e 53.0]

To display help: python scale.py -h

Short Usage: python scale.py [-h] ifile percentage [-o OFILE] [-e Latitude]
Usage: python scale.py [-h] ifile percentage [--OutputFilename OFILE] [--Extrapolate Latitude]

(arguments is [ ] are optional)