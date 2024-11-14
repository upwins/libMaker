from dotenv import load_dotenv

# import functions from specdal: https://specdal.readthedocs.io/en/latest/
import specdal
# import functions from asdreader: https://github.com/ajtag/asdreader
import asdreader

import importlib
importlib.reload(specdal);
importlib.reload(asdreader);

import os
import glob
import shutil
import pandas as pd
import numpy as np

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

MONGO_DB_URI = os.getenv('MONGO_DB_URI')

# codes for species with information and health\growth-stage\etc..
plant_codes = {
    'Ammo_bre': ['Ammophila', 'breviligulata', 'American Beachgrass', 'grass', 'https://en.wikipedia.org/wiki/Ammophila_breviligulata'],
    'Chas_lat': ['Chasmanthium', 'latifolium', 'River Oats', 'grass', 'https://en.wikipedia.org/wiki/Chasmanthium_latifolium'],
    'Pani_ama': ['Panicum', 'amarum', 'Coastal Panic Grass', 'grass', 'https://en.wikipedia.org/wiki/Panicum_amarum'],
    'Pani_vir': ['Panicum', 'virgatum', 'Switch Grass', 'grass', 'https://en.wikipedia.org/wiki/Panicum_virgatum'],
    'Soli_sem': ['Solidago', 'sempervirens', 'Seaside Goldenrod', 'succulent', 'https://en.wikipedia.org/wiki/Chasmanthium_latifolium'],
    'Robi_his': ['Robinia', 'hispida', 'Bristly locust', 'shrub', 'https://en.wikipedia.org/wiki/Robinia_hispida'],
    'More_pen': ['Morella', 'pennsylvanica', 'Bristly locust', 'shrub', 'https://en.wikipedia.org/wiki/Myrica_pensylvanica'],    
    'Rosa_rug': ['Rosa', 'rugosa', 'Sandy Beach Rose', 'shrub', 'https://en.wikipedia.org/wiki/Rosa_rugosa'],
    'Cham_fas': ['Chamaecrista', 'fasciculata', 'Partridge Pea', 'legume', 'https://en.wikipedia.org/wiki/Chamaecrista_fasciculata'],
    'Soli_rug': ['Solidago', 'rugosa', 'Wrinkleleaf goldenrod', 'shrub', 'https://en.wikipedia.org/wiki/Solidago_rugosa'],
    'Bacc_hal': ['Baccharis', 'halimifolia', 'Groundseltree', 'shrub', 'https://en.wikipedia.org/wiki/Baccharis_halimifolia'],
    'Iva_fru_': ['Iva', 'frutescens', 'Jesuits Bark ', 'shrub', 'https://en.wikipedia.org/wiki/Iva_frutescens'],
    'Ilex_vom': ['Ilex', 'vomitoria', 'Yaupon Holly', 'evergreen shrub', 'https://en.wikipedia.org/wiki/Ilex_vomitoria']
}  
growth_stage_codes = {  
    'PE': ['Post Germination Emergence', 'PE'],
	'RE': ['Re-emergence', 'RE'],
	'E': ['Emergence (from seed)', 'E'],
	'D': ['Dormant', 'D'],
	'1G': ['Year 1 growth', '1G'],
    '2G': ['Year 2 growth', '2G'],
	'1F': ['Year 1 Flowering', '1F'],
    'J': ['Juvenile', 'J'],
	'M': ['Mature', 'M']
}
principal_part_codes = {  
    'MX': ['Mix', 'MX'],
	'SA': ['Shoot Apex', 'SA'],
	'L': ['Leaf', 'L'],
	'IS': ['Internode Stem', 'IS'],
	'CS': ['Colar Sprout', 'CS'],
	'RS': ['Root Sprout', 'RS'],
	'LG': ['Lignin', 'LG'],
	'FL': ['Flower', 'FL'],
	'B': ['Blade', 'B'],
	'S': ['Seed', 'S'],
	'St': ['Stalk', 'St']
}
health_codes = { 
	'H': ['Healthy', 'H'],
    'MH': ['Mix Dormant Healthy', 'MH'],
	'DS': ['Drought Stress', 'DS'],
	'SS': ['Salt Stress (soak)', 'SS'],
    'SY': ['Salt Stress (spray)', 'SY'],
	'S': ['Stress', 'S'],
    'LLRZ': ['LLRZ Lab Stress', 'LLRZ'],
	'D': ['Dormant', 'D'],
    'R': ['Rust', 'R']
}

flower_codes = { 
	'FLG': ['Flowering', 'FLG'],
    'FRG': ['Fruiting', 'FRG'],
    "FFG": ['Fruiting and Flowering', 'FFG'],
    'N': ['Neither', 'N']
}
    
    
def read(filepath, jump_correct = False):
    # Reads a single ASD file with metadata.
    
    # check data
    if filepath[-4:] != '.asd':
        print(f'WARNING: File {fname} does not appear to be an ASD file.')
        return -1
    
    # read the asd file with specdal and asdreader
    s = specdal.Spectrum(filepath=filepath) 
    s_asdreader = asdreader.reader(filepath);
    fname = os.path.basename(filepath)

    if (jump_correct):
        wl = s.measurement.index

        # Fix 1: shift 0<wl<1000 range up/down to smooth jump at 1000
        i1 = np.where(wl==1000)[0][0]
        if not np.isnan(s.measurement.iloc[i1]):
            dp = ( ((s.measurement.iloc[i1+1]-s.measurement.iloc[i1+2]) + (s.measurement.iloc[i1-1]-s.measurement.iloc[i1]))/2 )
            d1 = (s.measurement.iloc[i1+1]-s.measurement.iloc[i1])
            s.measurement.iloc[:(i1+1)] = s.measurement.iloc[:(i1+1)] + dp + d1
        # Fix 2: shift 1800<wl<2500 range up/down to smooth jump at 1800
        i2 = np.where(wl==1800)[0][0]
        if not np.isnan(s.measurement.iloc[i2]):
            dp = ( ((s.measurement.iloc[i2+1]-s.measurement.iloc[i2+2]) + (s.measurement.iloc[i2-1]-s.measurement.iloc[i2]))/2 )
            d1 = (s.measurement.iloc[i2+1]-s.measurement.iloc[i2])
            s.measurement.iloc[(i2+1):] = s.measurement.iloc[(i2+1):] - dp - d1
    
    # Initial metadata population
    # compute a datetime string for the file name
    format_string = '%Y%m%d_%H%M%S'
    s.metadata['DateTimeUniqueIdentifier'] = s_asdreader.md.save_time.strftime(format_string)
    # compute a datetime string for the file name
    format_string = '%Y-%m-%d %H:%M:%S'    
    s.metadata['datetime_readable'] = s_asdreader.md.save_time.strftime(format_string)    
    s.metadata['instrument_num'] = s_asdreader.md.instrument_num    
    s.metadata['comment'] = s_asdreader.md.comment.decode("utf-8")
    s.metadata['principal_part_code'] = 'NA'
    s.metadata['principal_part_description'] = 'NA'
    s.metadata['growth_stage_code'] = 'NA' 
    s.metadata['growth_stage_description'] = 'NA'   
    s.metadata['health_code'] = 'NA'    
    s.metadata['health_description'] = 'NA'
    s.metadata['flower_code'] = 'NA'    
    s.metadata['flower_description'] = 'NA'  
    s.metadata['genus'] = 'NA'    
    s.metadata['species'] = 'NA'      
    s.metadata['common_name'] = 'NA'       
    s.metadata['category'] = 'NA'            
    s.metadata['sub-category'] = 'NA'     
    s.metadata['location'] = 'NA' 
    s.metadata['filenum'] = fname[-9:-4]
    s.metadata['url'] = 'NA'    
    
    
    # checking for specific target vegetation species
    # check if the filename begins with a target species Genus_species code (ignore case)
    for key in plant_codes.keys():
        if fname[:8].lower()==key.lower():
            s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes[key]
            s.metadata['category'] = 'target_vegetation'
            s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['MX'] # (default value)
            s.metadata['health_description'], s.metadata['health_code'] = health_codes['H'] # (default value)
            s.metadata['flower_description'], s.metadata['flower_code'] = flower_codes['N'] # (default value)
    # checking for specific informal or non - target species Genus_species code (ignore case)
    if ('beachgrass' in fname.lower()) or ('beach_grass' in fname.lower()):
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Ammo_bre']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['B']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'chamdecrista_fasc' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Cham_fas']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['L']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'partridgepea' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Cham_fas']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['L']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'panicum_amarum' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Pani_ama']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['B']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'coastalpanicum' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Pani_ama']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['B']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
        s.metadata['comment'] = s.metadata['comment']+'[not certain of species - check that spectrum is a match]'
    if 'ilexvomitoria' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Ilex_vom']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['MX']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'panicumvirgatum' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Pani_vir']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['MX']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'chasmanthiumlatifolium' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Chas_lat']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['MX']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'chasmanthium_lati' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Chas_lat']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['MX']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'chasmanthiu_latifoli' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Chas_lat']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['MX']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'panicum_vergatum' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Pani_vir']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['MX']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'panicum_virgatum' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Pani_vir']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['MX']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'solidago_semp' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Soli_sem']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['MX']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'iva_frutescens' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Iva_fru_']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['MX']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'baccharis_halimifolia' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Bacc_hal']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['MX']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'baccharis_halimif' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Bacc_hal']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['MX']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
    if 'solidago_rugosa' in fname.lower():
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['sub-category'], s.metadata['url'] = plant_codes['Bacc_hal']
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['MX']
        s.metadata['category'] = 'target_vegetation'
        s.metadata['health_code'] = 'H'  # (default value)    
        s.metadata['health_description'] = 'Healthy'  # (default value)
        
        
        
    
    # checking for growth stage codes
    for key in growth_stage_codes.keys():
        if '_'+key+'_' in fname:
            s.metadata['growth_stage_description'], s.metadata['growth_stage_code'] = growth_stage_codes[key]
    
    if 'mix of senesced and green' in s.metadata['comment'].lower():
        s.metadata['health_description'], s.metadata['health_code'] = health_codes['MH']
    
    if ('senesced portion' in fname.lower()) or ('greenAndSenesced' in s.metadata['comment'].lower()):
        s.metadata['health_description'], s.metadata['health_code'] = health_codes['MH']
    
    if ('y1g' in fname.lower()) or ('y1g' in s.metadata['comment'].lower()):
        s.metadata['growth_stage_description'], s.metadata['growth_stage_code'] = growth_stage_codes['1G']
            
    if ('dormant' in fname.lower()) or ('dormant' in s.metadata['comment'].lower()):
        s.metadata['growth_stage_description'], s.metadata['growth_stage_code'] = growth_stage_codes['D']
        s.metadata['health_description'], s.metadata['health_code'] = health_codes['D']
            
    if ('scenesed' in fname.lower()):
        s.metadata['growth_stage_description'], s.metadata['growth_stage_code'] = growth_stage_codes['D']
            
    if ('_scenesced0' in fname.lower()):
        s.metadata['growth_stage_description'], s.metadata['growth_stage_code'] = growth_stage_codes['D']
        s.metadata['health_description'], s.metadata['health_code'] = health_codes['D']
        
    if ('early-season-growth' in fname.lower()) or ('early-season-growth' in s.metadata['comment'].lower()):
        s.metadata['growth_stage_description'], s.metadata['growth_stage_code'] = growth_stage_codes['RE']
            
    if ('senesced portion' in fname.lower()) or ('senesced portion' in s.metadata['comment'].lower()):
        s.metadata['health_description'], s.metadata['health_code'] = health_codes['D']
    
    if ('mature' in fname.lower()) or ('mature' in s.metadata['comment'].lower()):
        s.metadata['growth_stage_description'], s.metadata['growth_stage_code'] = growth_stage_codes['M']
         
    if ('midseaseon' in fname.lower()) or ('midseaseon' in s.metadata['comment'].lower()):
        s.metadata['growth_stage_description'], s.metadata['growth_stage_code'] = growth_stage_codes['M']
        
    if ('midseason' in fname.lower()) or ('midseason' in s.metadata['comment'].lower()):
        s.metadata['growth_stage_description'], s.metadata['growth_stage_code'] = growth_stage_codes['M']
    
    if ('emergence' in fname.lower()) or ('emergence' in s.metadata['comment'].lower()):
        s.metadata['growth_stage_description'], s.metadata['growth_stage_code'] = growth_stage_codes['E']
         
    if ('sprout' in fname.lower()) or ('sprout' in s.metadata['comment'].lower()):
        s.metadata['growth_stage_description'], s.metadata['growth_stage_code'] = growth_stage_codes['E']
            
            	
    
    # checking for health codes
    for key in health_codes.keys():
        if ('_'+key+'_' in fname) or ('_'+key+'0' in fname):
            s.metadata['health_description'], s.metadata['health_code'] = health_codes[key]
            
    if ('stress' in fname.lower()) or ('stress' in s.metadata['comment'].lower()):
        s.metadata['health_description'], s.metadata['health_code'] = health_codes['S']
    
    if 'mix of senesced and green' in s.metadata['comment'].lower():
        s.metadata['health_description'], s.metadata['health_code'] = health_codes['MH']
    
    if ('rust' in fname.lower()) or ('rust' in s.metadata['comment'].lower()):
        s.metadata['health_description'], s.metadata['health_code'] = health_codes['R']
            
    
    # checking for flower codes
    for key in flower_codes.keys():
        if ('_'+key+'_' in fname) or ('_'+key+'0' in fname):
            s.metadata['flower_description'], s.metadata['flower_code'] = flower_codes[key]
    
    if ('_FL_0' in fname) or ('_FL0' in fname):
        s.metadata['flower_description'], s.metadata['flower_code'] = flower_codes['FLG']
    
    if ('_FR_0' in fname) or ('_FR0' in fname):
        s.metadata['flower_description'], s.metadata['flower_code'] = flower_codes['FRG']

    if ('_FF_0' in fname) or ('_FF0' in fname):
        s.metadata['flower_description'], s.metadata['flower_code'] = flower_codes['FFG']

    # checking for plant part codes
    for key in principal_part_codes.keys():
        if '_'+key+'_' in fname:
            s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes[key]
            
    if ('seedhead' in fname.lower()) or ('seedhead' in s.metadata['comment'].lower()):
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['S']
            
    if ('leaf' in fname.lower()) or ('leaf' in s.metadata['comment'].lower()):
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['L']
            
    if ('flower' in fname.lower()) or ('flower' in s.metadata['comment'].lower()):
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['FL']
        
    if ('blade' in fname.lower()) or ('blade' in s.metadata['comment'].lower()):
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['L']
        
    if ('stalk' in fname.lower()) or ('stalk' in s.metadata['comment'].lower()):
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['St']
        
    if ('stem' in fname.lower()) or ('stem' in s.metadata['comment'].lower()):
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['St']
        
    if '_mix0' in fname.lower():
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['MX']
        
    if ('bark' in fname.lower()) or ('bark' in s.metadata['comment'].lower()):
        s.metadata['principal_part_description'], s.metadata['principal_part_code'] = principal_part_codes['St']
        


    # checking for other material categories
    if ('soil' in fname.lower()) or ('soil' in s.metadata['comment'].lower()):
        s.metadata['category'] = 'soil'
        if 'plota' in fname.lower():
            s.metadata['sub-category'] = 'clay'
            s.metadata['location'] = 'PlotA'
        if 'plotb' in fname.lower():
            s.metadata['sub-category'] = 'clay'
            s.metadata['location'] = 'PlotB'
        if 'sand' in fname.lower():
            s.metadata['sub-category'] = 'golf-course-sand'
            s.metadata['location'] = 'Morven'
        if 'morven1_bg' in fname.lower():
            s.metadata['sub-category'] = 'clay'
            s.metadata['location'] = 'Morven'            
        
    if ('gravel_road' in fname.lower()) or ('gravel_road' in s.metadata['comment'].lower()):
        s.metadata['category'] = 'road'
        s.metadata['sub-category'] = 'gravel'
        s.metadata['location'] = 'Morven'
    
    if ('pasturegrass' in fname.lower()) or ('pasturegrass' in s.metadata['comment'].lower()):
        s.metadata['category'] = 'vegetation'
        s.metadata['sub-category'] = 'pasturegrass'
        s.metadata['location'] = 'Morven'
    
    if ('soy' in fname.lower()) or ('soy' in s.metadata['comment'].lower()):
        s.metadata['category'] = 'vegetation'
        s.metadata['sub-category'] = 'soybean'
        s.metadata['location'] = 'Morven'
        
    if ('soybean' in fname.lower()) or ('soybean' in s.metadata['comment'].lower()):
        s.metadata['category'] = 'vegetation'
        s.metadata['sub-category'] = 'soybean'
        s.metadata['location'] = 'Morven'
    
    if ('timothy' in fname.lower()) or ('timothy' in s.metadata['comment'].lower()):
        s.metadata['category'] = 'vegetation'
        s.metadata['sub-category'] = 'timothy'
        s.metadata['location'] = 'Morven'
    
    if ('milkweed' in fname.lower()) or ('milkweed' in s.metadata['comment'].lower()):
        s.metadata['category'] = 'vegetation'
        s.metadata['sub-category'] = 'milkweed'
        s.metadata['location'] = 'Morven'
        
    if ('backrounds' in fname.lower()) or ('backrounds' in s.metadata['comment'].lower()):
        s.metadata['category'] = 'vegetation'
        s.metadata['sub-category'] = 'backrounds'
        s.metadata['location'] = 'Morven'
    
    if ('vegetation' in fname.lower()) or ('timothy' in s.metadata['comment'].lower()):
        if s.metadata['category'] == 'NA':
            s.metadata['category'] = 'vegetation'
        
    if ('mugwart' in fname.lower()) or ('mugwart' in s.metadata['comment'].lower()):
        s.metadata['category'] = 'vegetation'
        s.metadata['sub-category'] = 'mugwart'
        s.metadata['location'] = 'Morven'        
        
    if ('specrral_reference_panel' in fname.lower()) or ('specrral_reference_panel' in s.metadata['comment'].lower()):
        s.metadata['category'] = 'manmade'
        s.metadata['sub-category'] = 'spectral-reference-panel'
            
    if ('styrafoam' in fname.lower()) or ('styrafoam' in s.metadata['comment'].lower()):
        s.metadata['category'] = 'manmade'
        s.metadata['sub-category'] = 'styrofoam'
            
    if ('iris' in fname.lower()) or ('iris' in s.metadata['comment'].lower()):
        s.metadata['category'] = 'vegetation'
        s.metadata['sub-category'] = 'iris'
            
    if ('grass_lawn' in fname.lower()) or ('grass_lawn' in s.metadata['comment'].lower()):
        s.metadata['category'] = 'vegetation'
        s.metadata['sub-category'] = 'grass'
    
   
    # checking for location
    if ('morven' in filepath.lower()) or ('morven' in s.metadata['comment'].lower()):
        s.metadata['location'] = 'Morven'
        
    if ('allied' in filepath.lower()) or ('allied' in s.metadata['comment'].lower()):
        s.metadata['location'] = 'Allied'

    # checking if collection is immediately after salt inundation
    if ('after salt' in filepath.lower()):
        s.metadata['comment'] = s.metadata['comment'] + "_after_salt_inundation"
        
    return s


def search_for_ASD_files(source = '', destination = ''):  
    # Creates a list of all ASD files stored on this computer
    fname_csv = destination+'filenames_asd.csv'
    
    print(f'Searching {source} and subdirectories for ASD files.') 
    
    # build a list of all ASD files in the source directory, including subdirectories
    fnames_asd = glob.glob(source+'**/*.asd', recursive=True)
    print(f'Number of ASD files found: {len(fnames_asd)}') 

    # iterate through all .asd file names and determine the UPWINS convention name
    # and print to a text file
    with open(fname_csv, 'w') as f:
        f.write('ASD fname\n')
        for filepath in fnames_asd:
            # write the filepath to the output csv file
            f.write(filepath+'\n') 
    f.close()
    print(f'Filenames saved in {fname_csv}')


def build_ASD_filename_UPWINS_convention_info(destination = ''):  
    # Reads a list of all ASD files on this computer from destination folder,
    # creates a dataframe with all the ASD filenames and corresponding 
    # UPWINS convention new names
    fname_not_readable_csv = destination+'filenames_not_readable.csv'
    fname_csv = destination+'filenames_asd.csv'   
    fname_UPWINS_csv = destination+'filenames_UPWINS_asd.csv'    
    print(f'Adding UPWINS convention filenames and metadata to {fname_csv}') 
    
    # create the dataFrame, starting with the file names in fname_csv
    df = pd.read_csv(fname_csv, index_col = False)
    df['ASD base_fname'] = ''
    df['comment'] = ''
    df['ASD UPWINS base_fname'] = ''
    df['category'] = ''
    df['sub-category'] = ''
    df['genus'] = ''
    df['species'] = ''
    df['principal_part'] = ''
    df['growth_stage'] = ''
    df['health'] = ''
    df['location'] = ''
    df['DateTimeUniqueIdentifier'] = ''
    df['Instrument #'] = ''
    df = df[['ASD base_fname', 'comment', 'ASD UPWINS base_fname', 'category', 'sub-category', 'genus', 'species', 'principal_part', 'growth_stage', 'health', 'location', 'DateTimeUniqueIdentifier', 'Instrument #', 'ASD fname']]

    # iterate through all .asd file names and determine the UPWINS convention name
    # and metadata
    not_readable_fnames = []
    df = df.reset_index()  # make sure indexes pair with number of rows
    for index, row in df.iterrows():
        filepath = row['ASD fname']
        
        #try:
        # read the spectrum information
        s = read(filepath)

        # create the new filename using the UPWINS convention
        if s.metadata['category'] == 'target_vegetation':
            fname_new = 'UPWINS'+\
                    '_'+\
                    s.metadata['genus']+\
                    '_'+\
                    s.metadata['species']+\
                    '_'+\
                    s.metadata['principal_part_code']+\
                    '_'+\
                    s.metadata['growth_stage_code']+\
                    '_'+\
                    s.metadata['health_code']+\
                    '_'+\
                    s.metadata['DateTimeUniqueIdentifier']+\
                    '.asd'
        else:
            fname_new = 'UPWINS'+\
                    '_'+\
                    s.metadata['category']+\
                    '_'+\
                    s.metadata['sub-category']+\
                    '_'+\
                    s.metadata['location']+\
                    '_'+\
                    s.metadata['DateTimeUniqueIdentifier']+\
                    '.asd'
            
        
        # fill in the basename for this ASD file
        df.at[index, 'ASD base_fname'] = os.path.basename(filepath)
        
        # fill in the ASD UPWINS base_fname for this ASD file
        df.at[index, 'ASD UPWINS base_fname'] = fname_new
        
        # fill in the category for this ASD file
        df.at[index, 'category'] = str(s.metadata['category'])
        
        # fill in the category for this ASD file
        df.at[index, 'sub-category'] = str(s.metadata['sub-category'])
        
        # fill in the comment for this ASD file
        df.at[index, 'comment'] = str(s.metadata['comment'])
        
        # fill in the genus for this ASD file
        df.at[index, 'genus'] = str(s.metadata['genus'])
        
        # fill in the species for this ASD file
        df.at[index, 'species'] = str(s.metadata['species'])
        
        # fill in the principal_part_code for this ASD file
        df.at[index, 'principal_part'] = str(s.metadata['principal_part_code'])
        
        # fill in the age_code for this ASD file
        df.at[index, 'growth_stage'] = str(s.metadata['growth_stage_code'])
        
        # fill in the health_code for this ASD file
        df.at[index, 'health'] = str(s.metadata['health_code'])
        
        # fill in the location for this ASD file
        df.at[index, 'location'] = str(s.metadata['location'])
        
        # fill in the DateTimeUniqueIdentifier for this ASD file
        df.at[index, 'DateTimeUniqueIdentifier'] = str(s.metadata['DateTimeUniqueIdentifier'])
        
        # fill in the basename for this ASD file
        df.at[index, 'Instrument #'] = str(s.metadata['instrument_num'])
            
        #except:
        #    not_readable_fnames.append(filepath)
    
    with open(fname_not_readable_csv, 'w') as f:
        for filepath in not_readable_fnames:
            # write the filepath to the output csv file
            f.write(filepath+'\n') 
    f.close()
    
    # drop any files that have duplicate values in 'ASD UPWINS base_fname' and 'Instrument #'
    # note: dropping by duplicates in 'ASD UPWINS base_fname' should be sufficient since that has unique data-time (to the second) identifier,
    # but including the instrument # as well just in case.
    
    df = df.drop_duplicates(['ASD UPWINS base_fname','Instrument #'], keep='last')
    df = df.sort_values(['category', 'sub-category', 'DateTimeUniqueIdentifier'], ascending=[False, False, True])
    df = df.drop(columns=['index'])
    
    # save the dataframe to a csv file
    df.to_csv(fname_UPWINS_csv, index=False)    
    print(f'Writing to {fname_UPWINS_csv} complete. There were {len(df)} unique files.')



def copy_rename_ASD_files(fname_UPWINS_csv = 'C:\\ASD_files\\filenames_UPWINS_asd.csv', source = 'C:\\ASD_files\\ASD_files_orig_names\\', destination = 'C:\\ASD_files\\ASD_files_UPWINS_names\\'):
    
    df = pd.read_csv(fname_UPWINS_csv, index_col = False, keep_default_na=False)
    for index, row in df.iterrows():
        fname_src = row['ASD fname'] 
        fname_base_src = row['ASD base_fname'] 
        fname_base_dst = row['ASD UPWINS base_fname'] 
        try:
            shutil.copyfile(fname_src, source+fname_base_src)
        except:
            pass
        shutil.copyfile(source+fname_base_src, destination+fname_base_dst)

'''
UPWINS_LatinGenus_latinspecies_PincipalPart_agecode_healthcode_DateTimeUniqueIdentifier

Principal Part Codes:
	Mix				MX
    Dicot - Woody Vines (ex. Rosa Rugosa)
    Shoot Apex 			SA
    Leaf 				L
    Internode Stem 		IS
    Colar Sprout		CS
    Root Sprout			RS
    Lignin 				LG
    Flower				FL
    Monocot - (ex. Chasmanthium, Panicum, )
    Blade 				B
    Seed 				S

Age Code:
	Post Germination Emergence 	PE
	Re-emergence			    RE
	Emergence (from seed)	    E
	Dormant 			        D
	Year 1 growth		        1G
	Year 1 Flowering	        1F
	Mature				        M

Health Code:
	Healthy 			    H 
	Drought Stress 		    DS
	Salt Stress			    SS
	SMixed Halthy\Stressed	MH
*For disease infestation or other plant specifics in terrestrial collection, please input information in metadata

Plant Code:
UPWINS_LatinGenus_latinspecies_PincipalPart_agecode_healthcode_DateTimeUniqueIdentifier
-	Use 4 letters for Genus, and 3 for Species 
-	Latin species can be lowercase 

Examples 
Bacc_hal_L_1G_H_00006
Ilex_vom_IS_RE_H_00001

Plant Codes:
Ammo_bre_SA_1G_H_DateTimeUniqueIdentifier
Bacc_hal_RS_1G_H_DateTimeUniqueIdentifier
Cham_fas_S_E_H_DateTimeUniqueIdentifier
Chas_lat_B_E_H_DateTimeUniqueIdentifier
Ilex_vom_IS_E_H_DateTimeUniqueIdentifier
Iva_fru_CS_RE_H_DateTimeUniqueIdentifier
More_pen_SA_PE_H_DateTimeUniqueIdentifier
Robi_his_SA_PE_H_DateTimeUniqueIdentifier
Rosa_rug_SA_1G_H_DateTimeUniqueIdentifier
Pani_vir_B_E_H_DateTimeUniqueIdentifier
Pani_ama_B_E_H_DateTimeUniqueIdentifier
Soli_sem_L_1G_H_DateTimeUniqueIdentifier
Soli_rug_L_1G_H_DateTimeUniqueIdentifier

For Non-Plant Collections
Specify Material, then Location. Examples:
Sand_Luegering Lettuce Farm_00001
Or
Material_Roadway_Farmname_00002
Plant Table for Reference:

Ammophila	breviligulata	American Beachgrass
Chasmanthium	latifolium	River Oats
Panicum	amarum	Coastal Panic Grass
Panicum 	virgatum	Switch Grass
Solidago	Sempervirens	Seaside Goldenrod 
Robinia 	hispida	Bristly locust 
Morella 	pennsylvanica	Northern Bayberry 
Rosa	rugosa	Sandy Beach Rose 
Chamaecrista 	fasciculata	Partridge Pea 
Solidago	Rugosa	Wrinkleleaf goldenrod 
Baccharis 	halimifolia	Groundseltree 
Iva 	frutescens	Jesuits Bark 
Ilex	vomitoria	Yaupon Holly 
'''



def build_UPWINS_ASD_database(destination = ''):  
    # Reads a list of all ASD files on this computer from destination folder,
    # creates a dataframe with all the ASD filenames and corresponding 
    # UPWINS convention new names
    fname_not_readable_csv = destination+'filenames_not_readable.csv'
    fname_csv = destination+'filenames_asd.csv'   
    fname_UPWINS_csv = destination+'UPWINS_ASD_database.csv'    
    print(f'Adding UPWINS convention filenames and metadata to {fname_csv}') 
    
    # create the dataFrame, starting with the file names in fname_csv
    df = pd.read_csv(fname_csv, index_col = False)
    df['ASD base_fname'] = ''
    df['comment'] = ''
    df['ASD UPWINS base_fname'] = ''
    df['category'] = ''
    df['sub-category'] = ''
    df['genus'] = ''
    df['species'] = ''
    df['principal_part'] = ''
    df['growth_stage'] = ''
    df['health'] = ''
    df['flower'] = ''
    df['location'] = ''
    df['DateTimeUniqueIdentifier'] = ''
    df['datetime_readable'] = ''
    df['Instrument #'] = ''
    df = df[['ASD UPWINS base_fname', 'datetime_readable', 'category', 'sub-category', 'genus', 'species', 'principal_part', 'growth_stage', 'health', 'flower', 'location', 'comment', 'DateTimeUniqueIdentifier', 'Instrument #', 'ASD base_fname', 'ASD fname']]

    # list of spectral data
    data = []

    # iterate through all .asd file names and determine the UPWINS convention name
    # and metadata
    not_readable_fnames = []
    df = df.reset_index()  # make sure indexes pair with number of rows
    for index, row in df.iterrows():
        filepath = row['ASD fname']
        
        #try:
        # read the spectrum information
        s = read(filepath, True)

        # create the new filename using the UPWINS convention
        if s.metadata['category'] == 'target_vegetation':
            fname_new = 'UPWINS'+\
                    '_'+\
                    s.metadata['genus']+\
                    '_'+\
                    s.metadata['species']+\
                    '_'+\
                    s.metadata['principal_part_code']+\
                    '_'+\
                    s.metadata['growth_stage_code']+\
                    '_'+\
                    s.metadata['health_code']+\
                    '_'+\
                    s.metadata['flower_code']+\
                    '_'+\
                    s.metadata['DateTimeUniqueIdentifier']+\
                    '.asd'
        else:
            fname_new = 'UPWINS'+\
                    '_'+\
                    s.metadata['category']+\
                    '_'+\
                    s.metadata['sub-category']+\
                    '_'+\
                    s.metadata['location']+\
                    '_'+\
                    s.metadata['DateTimeUniqueIdentifier']+\
                    '.asd'
            
        
        # fill in the basename for this ASD file
        df.at[index, 'ASD base_fname'] = os.path.basename(filepath)
        
        # fill in the ASD UPWINS base_fname for this ASD file
        df.at[index, 'ASD UPWINS base_fname'] = fname_new
        
        # fill in the category for this ASD file
        df.at[index, 'category'] = str(s.metadata['category'])
        
        # fill in the category for this ASD file
        df.at[index, 'sub-category'] = str(s.metadata['sub-category'])
        
        # fill in the comment for this ASD file
        df.at[index, 'comment'] = str(s.metadata['comment'])
        
        # fill in the genus for this ASD file
        df.at[index, 'genus'] = str(s.metadata['genus'])
        
        # fill in the species for this ASD file
        df.at[index, 'species'] = str(s.metadata['species'])
        
        # fill in the principal_part_code for this ASD file
        df.at[index, 'principal_part'] = str(s.metadata['principal_part_code'])
        
        # fill in the age_code for this ASD file
        df.at[index, 'growth_stage'] = str(s.metadata['growth_stage_code'])
        
        # fill in the health_code for this ASD file
        df.at[index, 'health'] = str(s.metadata['health_code'])

         # fill in the health_code for this ASD file
        df.at[index, 'flower'] = str(s.metadata['flower_code'])
        
        # fill in the location for this ASD file
        df.at[index, 'location'] = str(s.metadata['location'])
        
        # fill in the DateTimeUniqueIdentifier for this ASD file
        df.at[index, 'DateTimeUniqueIdentifier'] = str(s.metadata['DateTimeUniqueIdentifier'])
        
        # fill in the DateTimeUniqueIdentifier for this ASD file
        df.at[index, 'datetime_readable'] = str(s.metadata['datetime_readable'])
        
        # fill in the basename for this ASD file
        df.at[index, 'Instrument #'] = str(s.metadata['instrument_num'])
        
        # Add spectrum to data list
        record = {'ASD UPWINS base_fname':fname_new}
        measurement = s.measurement.to_dict()
        measurement = {str(k):v for k,v in measurement.items()}
        record.update(measurement)
        data.append(record)
        
        #except:
        #    not_readable_fnames.append(filepath)
    
    with open(fname_not_readable_csv, 'w') as f:
        for filepath in not_readable_fnames:
            # write the filepath to the output csv file
            f.write(filepath+'\n') 
    f.close()
    
    # drop any files that have duplicate values in 'ASD UPWINS base_fname' and 'Instrument #'
    # note: dropping by duplicates in 'ASD UPWINS base_fname' should be sufficient since that has unique data-time (to the second) identifier,
    # but including the instrument # as well just in case.
    
    print("Number of rows before dropping duplicates:", len(df))

    # Identify duplicate rows
    duplicates = df.duplicated(['ASD UPWINS base_fname','Instrument #'], keep=False)
    
    # Get duplicate rows
    duplicate_rows = df[duplicates]
    if (len(duplicate_rows) > 0): duplicate_rows.to_csv(destination+"duplicate_rows.csv", index=False)

    df = df.drop_duplicates(['ASD UPWINS base_fname','Instrument #'], keep='last')
    df = df.sort_values(['category', 'genus', 'species', 'DateTimeUniqueIdentifier'], ascending=[False, False, False, True])
    df = df.drop(columns=['index'])
    df = df.drop(columns=['ASD fname'])
    
    # save the dataframe to a csv file
    df.to_csv(fname_UPWINS_csv, index=False)    
    print(f'Writing to {fname_UPWINS_csv} complete. There were {len(df)} unique files.')

    df_data = pd.DataFrame.from_records(data)
    df_data = df_data.drop_duplicates(['ASD UPWINS base_fname'], keep='last')

    # save spectra to csv
    #df_data.to_csv(destination+'data.csv', index=True)

    data = df_data.to_dict('records')

    print("Length of data list:", len(data))

    # create list of dicts of metadata df
    metadata = df.to_dict('records')
    
    # import to mongodb
    mongoimport(metadata, data)

def mongoimport(metadata, data):
    
    uri = MONGO_DB_URI

    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

    db = client["upwins_db"]
    metadata_collection_name = "metadata"
    data_collection_name = "data"
    spectral_library_view_name = "spectral_library"

    metadata_collection = db[metadata_collection_name]
    data_collection = db[data_collection_name]
    spectral_library_view = db[spectral_library_view_name]

    if metadata_collection_name in db.list_collection_names():
        metadata_collection.drop()

    metadata_collection.insert_many(metadata)
    count = metadata_collection.count_documents({})
    print("Metadata doc count: ", count)

    if data_collection_name in db.list_collection_names():
        data_collection.drop()

    data_collection.insert_many(data)
    count = data_collection.count_documents({})
    print("Data doc count: ", count)

    if spectral_library_view_name in db.list_collection_names():
        spectral_library_view.drop()

    pipeline = [
        {
            '$lookup': {
                'from': 'data', 
                'localField': 'ASD UPWINS base_fname', 
                'foreignField': 'ASD UPWINS base_fname', 
                'as': 'spectrum'
            }
        }, {
            '$unwind': {
                'path': '$spectrum'
            }
        }, {
            '$project': {
                '_id': 0, 
                'spectrum._id': 0, 
                'spectrum.ASD UPWINS base_fname': 0
            }
        }
    ]

    db.create_collection(spectral_library_view_name, viewOn=metadata_collection_name, pipeline=pipeline)
    print("Spectral Library created.")

    client.close()