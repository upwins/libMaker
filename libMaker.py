# import functions from specdal: https://specdal.readthedocs.io/en/latest/
import specdal
# import functions from asdreader: https://github.com/ajtag/asdreader
import asdreader

import os

plant_codes = {
    'Ammo_bre': ['Ammophila', 'breviligulata', 'American Beachgrass', 'Grass', 'https://en.wikipedia.org/wiki/Ammophila_breviligulata'],
    'Chas_lat': ['Chasmanthium', 'latifolium', 'River Oats', 'Grass', 'https://en.wikipedia.org/wiki/Chasmanthium_latifolium'],
    'Pani_ama': ['Panicum', 'amarum', 'Coastal Panic Grass', 'Grass', 'https://en.wikipedia.org/wiki/Panicum_amarum'],
    'Pani_vir': ['Panicum', 'virgatum', 'Switch Grass', 'Grass', 'https://en.wikipedia.org/wiki/Panicum_virgatum'],
    'Soli_sem': ['Solidago', 'sempervirens', 'Seaside Goldenrod', 'succulent', 'https://en.wikipedia.org/wiki/Chasmanthium_latifolium'],
    'Robi_his': ['Robinia', 'hispida', 'Bristly locust', 'Shrub', 'https://en.wikipedia.org/wiki/Robinia_hispida'],
    'More_pen': ['Morella', 'pennsylvanica', 'Bristly locust', 'Shrub', 'https://en.wikipedia.org/wiki/Myrica_pensylvanica'],    
    'Rosa_rug': ['Rosa', 'rugosa', 'Sandy Beach Rose', 'Shrub', 'https://en.wikipedia.org/wiki/Rosa_rugosa'],
    'Cham_fas': ['Chamaecrista', 'fasciculata', 'Partridge Pea', 'Legume', 'https://en.wikipedia.org/wiki/Chamaecrista_fasciculata'],
    'Soli_rug': ['Solidago', 'rugosa', 'Wrinkleleaf goldenrod', 'Shrub', 'https://en.wikipedia.org/wiki/Solidago_rugosa'],
    'Bacc_hal': ['Baccharis', 'halimifolia', 'Groundseltree', 'Shrub', 'https://en.wikipedia.org/wiki/Baccharis_halimifolia'],
    'Iva_fru_': ['Iva', 'frutescens', 'Jesuits Bark ', 'Shrub', 'https://en.wikipedia.org/wiki/Iva_frutescens'],
    'Ilex_vom': ['Ilex', 'vomitoria', 'Yaupon Holly', 'Evergreen Shrub', 'https://en.wikipedia.org/wiki/Ilex_vomitoria']
}  

growth_stage_codes = {  
    'PE': ['Post Germination Emergence', 'PE'],
	'RE': ['Re-emergence', 'RE'],
	'E': ['Emergence (from seed)', 'E'],
	'D': ['Dormant', 'D'],
	'1G': ['Year 1 growth', '1G'],
	'1F': ['Year 1 Flowering', '1F'],
	'M': ['Mature', ' M']
}
    
def read(filepath):
    # check data
    if filepath[-4:] != '.asd':
        print(f'WARNING: File {fname} does not appear to be an ASD file.')
        return -1
    
    # read the asd file with specdal and asdreader
    s = specdal.Spectrum(filepath=filepath) 
    s_asdreader = asdreader.reader(filepath)
    fname = os.path.basename(filepath)
    
    # Initial metadata population
    # compute a datetime string for the file name
    format_string = '%Y%m%d_%H%M%S'
    s.metadata['DateTimeUniqueIdentifier'] = s_asdreader.md.save_time.strftime(format_string)
    # compute a datetime string for the file name
    format_string = '%Y-%m-%d %H:%M:%S'    
    s.metadata['datetime_readable'] = s_asdreader.md.save_time.strftime(format_string)    
    s.metadata['instrument_num'] = s_asdreader.md.instrument_num    
    s.metadata['comment'] = s_asdreader.md.comment.decode("utf-8")
    s.metadata['principal_part_code'] = 'MX' # defaut value
    s.metadata['age_code'] = 'Unknown' 
    s.metadata['age_description'] = 'Unknown'   
    s.metadata['health_code'] = 'Unknown'    
    s.metadata['vegetation_type'] = 'Unknown' 
    s.metadata['genus'] = 'Unknown'    
    s.metadata['species'] = 'Unknown'      
    s.metadata['common_name'] = 'Unknown' 
    s.metadata['filenum'] = fname[-9:-4]
    s.metadata['url'] = 'Unknown'    
    
    # checking for specific target species
    # check if the filename begins with a target species Genus_species code (ignore case)
    for key in plant_codes_dict.keys():
        if fname[:8].lower()==key.lower():
            s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['vegetation_type'], s.metadata['url'] = plant_codes_dict[key]
    # checking for specific informal or non - target species Genus_species code (ignore case)
    if ('beachgrass' in fname.lower()):
        s.metadata['genus'], s.metadata['species'], s.metadata['common_name'], s.metadata['vegetation_type'], s.metadata['url'] = plant_codes_dict['Ammo_bre']
    
    # checking for health codes
    for key in growth_stage_codes.keys():
        if '_'+key+'_' in fname:
            s.metadata['age_description'], s.metadata['age_code'] = growth_stage_codes[key]
    if ('dormant' in fname.lower()) or ('dormant' in s.metadata['comment'].lower()):
        s.metadata['age_description'], s.metadata['age_code'] = growth_stage_codes['D']

    return s




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
	Healthy 			H 
	Drought Stress 		DS
	Salt Stress			SS
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