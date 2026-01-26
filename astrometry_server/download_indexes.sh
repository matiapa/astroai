#! /bin/bash

cd indexes

# index-5206-*
for ((i=0; i<48; i++)); do
    I=$(printf %02i $i)
    wget https://portal.nersc.gov/project/cosmo/temp/dstn/index-5200/LITE/index-5206-$I.fits
done
~        
