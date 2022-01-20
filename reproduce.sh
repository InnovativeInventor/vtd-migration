python migrate.py MI ~/git/MI-shapefiles/MI.zip
python migrate.py VA ~/git/VA-shapefiles/VA_precincts.zip
python migrate.py AK ~/git/AK-shapefiles/AK_precincts.zip --repair
python migrate.py IN ~/git/IN-shapefiles/Indiana.zip
python migrate.py IN source/in_2020.shp --vtd-loc products/IN_vtd20.shp --ignore-top-issues
python migrate.py IN source/in_2018.shp --vtd-loc products/IN_vtd20.shp --ignore-top-issues
python migrate.py UT ~/git/UT-shapefiles/UT_precincts.zip
python migrate.py AZ ~/git/AZ-shapefiles/az_precincts.zip
python migrate.py NM ../NM-shapefiles/new_mexico_precincts.zip --vtd-loc ../nm-precincts/nm_precincts.shp --output-loc products/nm_precincts_with_elections.shp
python migrate.py MA ~/git/VRA-data-products/Massachusetts/shapes/MA_pcts.shp --include-cvap
python migrate.py MD ../MD-shapefiles/MD_precincts_abs.zip
python migrate.py LA ~/git/LA-shapefiles/LA_1519.zip
python migrate.py TX source/TX_vtds.zip
python migrate.py CT ../CT-shapefiles/CT_precincts.zip
python migrate.py DE ../DE-shapefiles/DE_precincts.zip
python migrate.py GA ../GA-shapefiles/GA_precincts.zip
python migrate.py NC ../NC-shapefiles/NC_VTD.zip
python migrate.py MN ../MN-shapefiles/MN12_18.zip
python migrate.py NE ../NE-shapefiles/NE.zip
python migrate.py NH ../NH-shapefiles/NH.zip
python migrate.py OK ../OK-shapefiles/OK_precincts.zip
python migrate.py RI ../RI-shapefiles/RI_precincts.zip
python migrate.py GA ~/git/GA-shapefiles/GA_precincts.zip

python migrate.py MD ~/Dropbox/mggg/MD_precincts_full/MD_precincts_full.shp --vtd-loc products/MD_vtd20.shp

python migrate.py OH source/OH16_gen.zip --drop-na --repair
python migrate.py OH source/OH18_gen.zip --drop-na --vtd-loc products/OH_vtd20.shp --repair
python migrate.py OH source/OH18_prime.zip --drop-na --vtd-loc products/OH_vtd20.shp --repair
python migrate.py OH source/OH20_all.zip --drop-na --vtd-loc products/OH_vtd20.shp --repair

python migrate.py OK ../OK-shapefiles/OK_precincts.zip --ignore-top-issues
python migrate.py MO ../MO-shapefiles/MO_vtds.zip

python migrate.py WI ../WI-shapefiles/WI_2020_wards.zip
python migrate.py WI ~/Dropbox/mggg/WI/WI_DATA/shp/WI_DATA.shp --vtd-loc products/WI_vtd20.shp

python migrate.py PA source/pa_2016.zip 
python migrate.py PA source/pa_2018.zip --vtd-loc products/PA_vtd20.shp
python migrate.py PA source/pa_2020.zip --vtd-loc products/PA_vtd20.shp --export-blocks
