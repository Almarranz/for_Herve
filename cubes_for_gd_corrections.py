#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 16:18:34 2024

@author: amartinez
"""

import astropy.io.fits as fits
import numpy as np
import os
import sys
from astropy.table import Table
from astropy.wcs.utils import fit_wcs_from_points
from astropy.wcs import WCS
from astropy.io import fits
import astroalign as aa
from astropy.coordinates import SkyCoord
import astropy.units as u
import matplotlib.pyplot as plt
from astropy.wcs.utils import fit_wcs_from_points
import shutil
import gzip
# %
# %%
folder = '/Users/amartinez/Desktop/for_people/for_Herve/gns2/F20/'
pruebas = '/Users/amartinez/Desktop/for_people/for_Herve/pruebas/'
sf_folder = '/Users/amartinez/Desktop/for_people/for_Herve/gns2/F20/stars_lists/'
clean = '/Users/amartinez/Desktop/for_people/for_Herve/gns2/F20/cleaned/'
VVV_fol = '/Users/amartinez/Desktop/PhD/Catalogs/VVV/b333/PMS/'

###########IMPORTANT################
# list of raw images is in /home/data/raw/GNS_2/H/Field/20
####################################
field = 20

vvv = Table.read(VVV_fol + 'b333.dat', format = 'ascii')
lista = open(folder + 'list.txt', 'r')
lines = len(lista.readlines())# This is closing lista. I have to reopen it
lista = open(folder + 'list.txt', 'r')
# %%
primary_hdu_c1 = fits.PrimaryHDU()
list_of_hdu_c1 = [primary_hdu_c1]
primary_hdu_c2 = fits.PrimaryHDU()
list_of_hdu_c2 = [primary_hdu_c2]
primary_hdu_c3 = fits.PrimaryHDU()
list_of_hdu_c3 = [primary_hdu_c3]
primary_hdu_c4 = fits.PrimaryHDU()
list_of_hdu_c4 = [primary_hdu_c4]
for li,l in enumerate(lista):
    print(30*'*')
    print(f'Working on file {li+1}/{lines}')
    print(30*'*')
    
    orig_header = fits.getheader(folder + l.strip())
    print(li)
    with gzip.open(clean + 'cube%s.fits.gz'%(li+1),'rb') as f_in:
        with open(clean + 'cube%s.fits'%(li+1),'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
            
    # with fits.open(clean + 'cube%s.fits'%(li+1),mode = 'update') as cube:
    #     cube[0].header = orig_header
    #     cube.flush()   
        # cube.writeto(clean + 'cube%s.fits.gz'%(li+1), overwrite = True)
    cube = fits.open(clean + 'cube%s.fits'%(li+1),mode = 'update') 
    cube[0].header = orig_header
    cube.flush()   
    image_data = cube[0].data
    wcs = WCS(cube[0].header, naxis = 2)
    naxis1 = cube[0].header['NAXIS1']
    naxis2 = cube[0].header['NAXIS2']
    x_off = cube[0].header['CRPIX2']
    y_off = cube[0].header['CRPIX1']
    
    use_idx = vvv['J']<900
    vvv_data = vvv[use_idx]
    
    vvv_ra = vvv_data['ra']
    vvv_dec = vvv_data['dec']
    # vvv_gal = SkyCoord(ra = vvv_ra, dec = vvv_dec, unit = 'degree').galactic 
    
    xy = wcs.all_world2pix(np.c_[vvv_data['ra'],vvv_data['dec']],1)
    x = xy[:,0]
    y = xy[:,1]
    
    
    vvv_data.add_columns((xy[:,0],xy[:,1]),names = ('x','y'))
    
    mask = ((x >= -x_off) & (x < naxis1-x_off) & (y >= 0) & (y < naxis2))
    
    # Apply the mask to the vvv.txt data
    vvv_overlap = vvv_data[mask]
    
    
    vvv_overlap.sort('J')
    
    x_vvv = vvv_overlap['x']
    y_vvv = vvv_overlap['y']
    # xh = naxis1/2
    
    
    xh = (max(x_vvv) + min(x_vvv))/2
    yh = (max(y_vvv) + min(y_vvv))/2
    #crop list for each chip
    for chip in range(1,3):
        primary_hdu = fits.PrimaryHDU()
        list_of_hdu = [primary_hdu]
        if (chip == 1):
            idx = np.nonzero((x_vvv < xh) & (y_vvv < yh))
        elif (chip == 2):
            idx = np.nonzero((x_vvv > xh) & (y_vvv < yh))
        elif (chip == 3):
            idx = np.nonzero((x_vvv > xh) & (y_vvv > yh))
        elif (chip == 4):
            idx = np.nonzero((x_vvv < xh) & (y_vvv > yh))
        #
        fig, ax = plt.subplots(1,1)
        ax.scatter(x_vvv,y_vvv)
        ax.scatter(x_vvv[idx],y_vvv[idx])
        ax.axvline(xh, color = 'r')
        
        gns = Table.read(sf_folder + 'dejitter_stars_%s_%s.txt'%(chip,li+1), format = 'ascii')
        #This ara the xy coordinates from starfinder on the original cubes
        x_gns = gns['x']
        y_gns = gns['y']
        
        xy_gns = np.c_[x_gns,y_gns]
        
        xy_vvv = np.vstack((vvv_overlap['x'][idx],vvv_overlap['y'][idx])).T
        # Astroalign does not work when repeated value appears in the same array
        xy_test, idx_u, = np.unique(xy_vvv, axis=0, return_index=True)
        xy_vvv_unique = xy_vvv[np.sort(idx_u)]
        # sys.exit(154)
        # fig, ax = plt.subplots(1,1)
        # ax.scatter(xy_vvv[:,0],xy_vvv[:,1], s =20)
        # ax.scatter(xy_vvv_unique[:,0],xy_vvv_unique[:,1], s =1)
        
        # sys.exit(154)
        p, (pos_img, pos_img_t) = aa.find_transform(xy_gns, xy_vvv_unique, max_control_points=200)
        
        
        fig, (ax1,ax2) = plt.subplots(1,2)
        ax1.scatter(pos_img[:,0],pos_img[:,1])
        ax2.scatter(pos_img_t[:,0],pos_img_t[:,1])
        
        # Find the common VVV stars in the VVV table to retrive the RA and Dec coordinates
        # x_vvv = pos_img_t  # 
        
    
        x_overlap = np.array(vvv_overlap['x'][idx])
        y_overlap = np.array(vvv_overlap['y'][idx])
        
    
        indices = []
        
    
        for coord in pos_img_t:
            x, y = coord
            # Find the indices where both x and y match in vvv_overlap
            index = np.where((x_overlap == x) & (y_overlap == y))[0]
            
            # If a match is found, append the index
            if index.size > 0:
                indices.append(index[0])  # Assuming one-to-one match
            else:
                indices.append(-1)  # Append -1 for unmatched points
        
        # Convert indices list to numpy array for easier handling
        indices = np.array(indices)
        
        # Print or return the indices
        print(indices)
        vvv_com = vvv_overlap[idx][indices]
        vvv_com.write(pruebas + 'vvv_common_c%s.txt'%(chip), format = 'ascii', overwrite = True)
        
        
        gns_com_xy = Table(pos_img, names = ('x','y'))
        vvv_com_xy = Table(pos_img_t, names = ('x','y'))
        gns_com_xy.write(pruebas + 'gns_c%s_com.txt'%(chip), format = 'ascii',overwrite=True)
        vvv_com_xy.write(pruebas + 'vvv_c%s_com.txt'%(chip), format = 'ascii',overwrite=True)
        
    
        vvv_com_ad = SkyCoord(ra = vvv_com['ra'],dec = vvv_com['dec'],unit = 'degree')
        xy_com = np.vstack((pos_img[:,0],pos_img[:,1]))
        wcs_new = fit_wcs_from_points(xy_com, vvv_com_ad, projection="TAN")
        
        data_cube = cube[0].data
        header = cube[0].header  # Get the header from the corresponding extension
        for i in range(cube[0].header['NAXIS3']):
            # Get the data and header for each image (extension)
            if chip ==1:
                data = data_cube[i][0:2048,0:2048]# Use i+1 since the first is the PrimaryHDU
               
            if chip == 2:
                data = data_cube[i][0:2048,2048:]
                
            if chip == 3:
                data = data_cube[i][2048:,2048:]
               
            if chip == 4:
                data = data_cube[i][2048:,0:2048]
        
        wcs_header = wcs_new.to_header()
        
        for card in wcs_header.cards:
            # If the key already exists, it will be replaced, otherwise it will be added
            header[card.keyword] = card.value
        # Create an ImageHDU with the data and the corresponding header
        # image_hdu = fits.ImageHDU(data=data, header=wcs_header)
        image_hdu = fits.ImageHDU(data=data, header=header)
        
        # Add the new ImageHDU to the HDUList
        list_of_hdu.append(image_hdu)

        # Create the HDUList object
        combined_hdul = fits.HDUList(list_of_hdu)
        
    combined_hdul.writeto(pruebas  +'%s_pointings_f20_c%s.fits'%(len(lines),chip), overwrite=True)
    print('FITS file F%sc%s created.'%(field, chip))
    
    sys.exit()
        
        
        
        
        