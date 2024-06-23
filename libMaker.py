# import functions from specdal: https://specdal.readthedocs.io/en/latest/
import specdal
# import functions from asdreader: https://github.com/ajtag/asdreader
import asdreader

def read(fname):
    # read the asd file with specdal
    s = specdal.Spectrum(filepath=fname)
    
    # read the asd file with asdreader
    s_asdreader = asdreader.reader(fname)
    
    # compute a datetime string for the file name
    format_string = '%Y%m%d_%H%M%S'
    s.metadata['DateTimeUniqueIdentifier'] = s_asdreader.md.save_time.strftime(format_string)
    
    # compute a datetime string for the file name
    format_string = '%Y-%m-%d %H:%M:%S'
    s.metadata['datetime_readable'] = s_asdreader.md.save_time.strftime(format_string)
    
    s.metadata['instrument_num'] = s_asdreader.md.instrument_num
    
    s.metadata['comment'] = s_asdreader.md.comment
    
    s.metadata['principal_part_code'] = 'None'
    
    s.metadata['age_code'] = 'None'
    
    s.metadata['health_code'] = 'None'
    
    s.metadata['genus'] = 'None'
    
    s.metadata['species'] = 'None'
    
    s.metadata['common_name'] = 'None'
    
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
Solidago	Sempervirens	Seaside Goldenrod (Soli_sem)
Robinia 	hispida	Bristly locust (Robi_his)
Morella 	pennsylvanica	Northern Bayberry (More_pen)
Rosa	rugosa	Sandy Beach Rose (Rosa_rug)
Chamaecrista 	fasciculata	Partridge Pea (Cham_fas)
Solidago	Rugosa	Wrinkleleaf goldenrod (Soli_sem)
Baccharis 	halimifolia	Groundseltree (Bacc_hal)
Iva 	frutescens	Jesuits Bark (Iva_fru)
Ilex	vomitoria	Yaupon Holly (Ilex_vom)
'''