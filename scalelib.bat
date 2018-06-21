rem This program does: 
rem - scale WAsP Libs by an energy percentage x (v*x^(1/3)) - enter percentage as 89 instead of 0.89 or 89%
rem - generate gwc 
rem - with option "-e Latitude", it extrapolates to the roughness length of 1.5m 
rem
rem Example: python scale.py testlib.lib 110 [-e 53.0] 
rem
rem To display help: python scale.py -h
rem
rem Short Usage: python scale.py [-h] ifile percentage [-o OFILE] [-e Latitude]
rem Usage: python scale.py [-h] ifile percentage [--OutputFilename OFILE] [--Extrapolate Latitude] 
rem
rem (arguments in [ ] are optional)

rem Without extrapolation:
python scale.py testlib.lib 95.5

rem With extrapolation:
python scale.py testlib.lib 95.5 -e 53.0

pause