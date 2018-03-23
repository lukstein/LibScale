rem This program does:
rem - scale WAsP Libs by an energy percentage x (v*x^(1/3)) - enter percentage as 89.5 instead of 0.895 or 89.5%
rem - generate gwc
rem 
rem Example: python scale.py testlib.lib 110
rem 
rem To display help: python scale.py -h
rem 
rem Short Usage: python scale.py [-h] ifile percentage [-o OFILE]
rem Usage: python scale.py [-h] ifile percentage [--OutputFilename OFILE]
rem 
rem (arguments is [ ] are optional)

python scale.py testlib.lib 95.5
pause