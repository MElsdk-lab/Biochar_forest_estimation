# =======================================================
# gee_functions.py
# University of Pittsburgh | Biochar Feedstock Methodology
# All GEE export functions — importable from any notebook
# =======================================================
# Usage:
#   from gee_functions import (
#       prepare_forest_collection,
#       export_forest_area,
#       prepare_states_forest_collection,
#       export_states_forest_area,
#       get_forest_cover_bins_one_country,
#       export_forest_cover_bins_all_countries,
#       get_forest_cover_bins_one_state,
#       export_forest_cover_bins_all_states,
#       get_forest_cover_area_type_country,
#       export_forest_cover_area_type_all_countries,
#       get_forest_cover_area_type_state,
#       export_forest_cover_area_type_all_states,
#       get_forest_area_bin_type_state,
#       export_forest_area_bin_type_all_states,
#   )
# =======================================================

import ee
from data_config import get_all_countries

# NOTE: These functions depend on the following GEE objects
# being initialized before calling them:
#   - treecover2000_masked
#   - datamask
#   - glc_2000


# ── SECTION 1: Forest Area by Threshold — Countries ───────────────────────────

def prepare_forest_collection(selected_regions, threshold):
    """
    Prepare a GEE FeatureCollection with forest area per country
    for a given canopy cover threshold.
    Returns a GEE object (not yet computed).
    """
    all_countries = get_all_countries(selected_regions)

    lsib_fao = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017') \
                 .filter(ee.Filter.inList('country_na', all_countries))

    forest_mask = treecover2000_masked.gte(threshold).selfMask().updateMask(datamask.eq(1))
    area_image  = forest_mask.multiply(ee.Image.pixelArea().divide(1e10))

    region_areas = area_image.reduceRegions(
        collection=lsib_fao,
        reducer=ee.Reducer.sum(),
        scale=30,
    )
    region_areas = region_areas.map(lambda f: f.set('threshold', threshold))
    return region_areas


def export_forest_area(selected_regions, thresholds, region_label='all_countries'):
    """
    Merge all thresholds into one FeatureCollection and
    submit a single export task to Google Drive.
    Output columns: country_na, threshold, sum
    """
    combined = ee.FeatureCollection([])

    for threshold in thresholds:
        result = prepare_forest_collection(selected_regions, threshold)
        combined = combined.merge(result)

    filename = f'forest_area_thresholds_{region_label}'
    task = ee.batch.Export.table.toDrive(
        collection=combined,
        description=filename,
        folder='GEE_exports',
        fileNamePrefix=filename,
        fileFormat='CSV',
        selectors=['country_na', 'threshold', 'sum']
    )
    task.start()
    print(f'✅ Single export task submitted: {filename}')
    return task


# ── SECTION 2: Forest Area by Threshold — US States ───────────────────────────

def prepare_states_forest_collection(selected_states, threshold):
    """
    Prepare a GEE FeatureCollection with forest area per US state
    for a given canopy cover threshold.
    Returns a GEE object (not yet computed).
    """
    tiger_states = ee.FeatureCollection('TIGER/2018/States') \
                     .filter(ee.Filter.inList('NAME', selected_states))

    forest_mask = treecover2000_masked.gte(threshold).selfMask().updateMask(datamask.eq(1))
    area_image  = forest_mask.multiply(ee.Image.pixelArea().divide(1e10))

    states_areas = area_image.reduceRegions(
        collection=tiger_states,
        reducer=ee.Reducer.sum(),
        scale=30,
        maxPixelsPerRegion=1e13
    )
    states_areas = states_areas.map(lambda f: f.set('threshold', threshold))
    return states_areas


def export_states_forest_area(selected_states, thresholds, region_label='all_states'):
    """
    Merge all thresholds into one FeatureCollection and
    submit a single export task to Google Drive.
    Output columns: NAME, threshold, sum
    """
    combined = ee.FeatureCollection([])

    for threshold in thresholds:
        result = prepare_states_forest_collection(selected_states, threshold)
        combined = combined.merge(result)

    filename = f'states_forest_area_thresholds_{region_label}'
    task = ee.batch.Export.table.toDrive(
        collection=combined,
        description=filename,
        folder='GEE_exports',
        fileNamePrefix=filename,
        fileFormat='CSV',
        selectors=['NAME', 'threshold', 'sum']
    )
    task.start()
    print(f'✅ Single export task submitted: {filename}')
    return task


# ── SECTION 3: Forest Cover Distribution by Bin — Countries ───────────────────

def get_forest_cover_bins_one_country(country_feature, bins):
    """
    For one country feature, compute forest area (Mha) per canopy cover bin.
    Returns a GEE FeatureCollection — one Feature per bin.
    """
    all_features = ee.FeatureCollection([])

    for i in range(len(bins) - 1):
        bin_label = f'{bins[i]}-{bins[i+1]}'

        forest_mask_bin = (
            treecover2000_masked.gte(bins[i])
            .And(treecover2000_masked.lt(bins[i+1]))
            .selfMask()
            .updateMask(datamask.eq(1))
        )

        area_image = forest_mask_bin.multiply(ee.Image.pixelArea().divide(1e10))

        region_area = area_image.reduceRegions(
            collection=ee.FeatureCollection([country_feature]),
            reducer=ee.Reducer.sum(),
            scale=30
        )

        region_area = region_area.map(lambda f: f.set('bin', bin_label))
        all_features = all_features.merge(region_area)

    return all_features


def export_forest_cover_bins_all_countries(selected_regions, bins, region_label='all_countries'):
    """
    Loop over all countries, build one combined FeatureCollection,
    and submit a single export task to Drive.
    Output columns: country_na, bin, sum
    """
    all_countries = get_all_countries(selected_regions)

    lsib_fao = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017') \
                  .filter(ee.Filter.inList('country_na', all_countries))

    country_list = lsib_fao.toList(lsib_fao.size())
    n = lsib_fao.size().getInfo()

    combined = ee.FeatureCollection([])

    for i in range(n):
        country_feature = ee.Feature(country_list.get(i))
        result = get_forest_cover_bins_one_country(country_feature, bins)
        combined = combined.merge(result)

    filename = f'forest_cover_bins_{region_label}'
    task = ee.batch.Export.table.toDrive(
        collection=combined,
        description=filename,
        folder='GEE_exports',
        fileNamePrefix=filename,
        fileFormat='CSV',
        selectors=['country_na', 'bin', 'sum']
    )
    task.start()
    print(f'✅ Single export task submitted: {filename}')
    return task


# ── SECTION 4: Forest Cover Distribution by Bin — US States ───────────────────

def get_forest_cover_bins_one_state(state_feature, bins):
    """
    For one state feature, compute forest area (Mha) per canopy cover bin.
    Returns a GEE FeatureCollection — one Feature per bin.
    """
    all_features = ee.FeatureCollection([])

    for i in range(len(bins) - 1):
        bin_label = f'{bins[i]}-{bins[i+1]}'

        forest_mask_bin = (
            treecover2000_masked.gte(bins[i])
            .And(treecover2000_masked.lt(bins[i+1]))
            .selfMask()
            .updateMask(datamask.eq(1))
        )

        area_image = forest_mask_bin.multiply(ee.Image.pixelArea().divide(1e10))

        region_area = area_image.reduceRegions(
            collection=ee.FeatureCollection([state_feature]),
            reducer=ee.Reducer.sum(),
            scale=30
        )

        region_area = region_area.map(lambda f: f.set('bin', bin_label))
        all_features = all_features.merge(region_area)

    return all_features


def export_forest_cover_bins_all_states(selected_states, bins, region_label='all_states'):
    """
    Loop over all states, build one combined FeatureCollection,
    and submit a single export task to Drive.
    Output columns: NAME, bin, sum
    """
    tiger_states = ee.FeatureCollection('TIGER/2018/States') \
                     .filter(ee.Filter.inList('NAME', selected_states))

    state_list = tiger_states.toList(tiger_states.size())
    n = tiger_states.size().getInfo()

    combined = ee.FeatureCollection([])

    for i in range(n):
        state_feature = ee.Feature(state_list.get(i))
        result = get_forest_cover_bins_one_state(state_feature, bins)
        combined = combined.merge(result)

    filename = f'forest_cover_bins_{region_label}'
    task = ee.batch.Export.table.toDrive(
        collection=combined,
        description=filename,
        folder='GEE_exports',
        fileNamePrefix=filename,
        fileFormat='CSV',
        selectors=['NAME', 'bin', 'sum']
    )
    task.start()
    print(f'✅ Single export task submitted: {filename}')
    return task


# ── SECTION 5: Forest Area by GLC Forest Type — Countries ─────────────────────

def get_forest_cover_area_type_country(country_feature, forest_classification):
    """
    For one country feature, compute forest area (Mha) per GLC forest type.
    Returns a GEE FeatureCollection — one Feature with one column per class.
    """
    class_images = []
    for fc in forest_classification:
        class_mask = glc_2000.eq(fc['code']).selfMask()
        class_area = class_mask.multiply(ee.Image.pixelArea().divide(1e10)).rename(fc['name'])
        class_images.append(class_area)

    multi_band_image = ee.Image.cat(class_images)

    region_area = multi_band_image.reduceRegions(
        collection=ee.FeatureCollection([country_feature]),
        reducer=ee.Reducer.sum(),
        scale=30
    )
    return region_area


def export_forest_cover_area_type_all_countries(selected_regions, forest_classification, region_label='all_countries'):
    """
    Loop over all countries, build one combined FeatureCollection,
    and submit a single export task to Drive.
    Output columns: country_na + one column per GLC forest class
    """
    all_countries = get_all_countries(selected_regions)
    lsib_fao = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017') \
                  .filter(ee.Filter.inList('country_na', all_countries))
    country_list = lsib_fao.toList(lsib_fao.size())
    n = lsib_fao.size().getInfo()

    combined = ee.FeatureCollection([])
    for i in range(n):
        country_feature = ee.Feature(country_list.get(i))
        result = get_forest_cover_area_type_country(country_feature, forest_classification)
        combined = combined.merge(result)

    selectors = ['country_na'] + [fc['name'] for fc in forest_classification]
    filename = f'forest_cover_area_type_{region_label}'

    country_task = ee.batch.Export.table.toDrive(
        collection=combined,
        description=filename,
        folder='GEE_exports',
        fileNamePrefix=filename,
        fileFormat='CSV',
        selectors=selectors
    )
    country_task.start()
    print(f'✅ Single export task submitted: {filename}')
    return country_task


# ── SECTION 6: Forest Area by GLC Forest Type — US States ─────────────────────

def get_forest_cover_area_type_state(state_feature, forest_classification):
    """
    For one state feature, compute forest area (Mha) per GLC forest type.
    Returns a GEE FeatureCollection — one Feature with one column per class.
    """
    class_images = []
    for fc in forest_classification:
        class_mask = glc_2000.eq(fc['code']).selfMask()
        class_area = class_mask.multiply(ee.Image.pixelArea().divide(1e10)).rename(fc['name'])
        class_images.append(class_area)

    multi_band_image = ee.Image.cat(class_images)

    region_area = multi_band_image.reduceRegions(
        collection=ee.FeatureCollection([state_feature]),
        reducer=ee.Reducer.sum(),
        scale=30
    )
    return region_area


def export_forest_cover_area_type_all_states(selected_states, forest_classification, region_label='all_states'):
    """
    Loop over all states, build one combined FeatureCollection,
    and submit a single export task to Drive.
    Output columns: NAME + one column per GLC forest class
    """
    tiger_states = ee.FeatureCollection('TIGER/2018/States') \
                     .filter(ee.Filter.inList('NAME', selected_states))
    state_list = tiger_states.toList(tiger_states.size())
    n = tiger_states.size().getInfo()

    combined = ee.FeatureCollection([])
    for i in range(n):
        state_feature = ee.Feature(state_list.get(i))
        result = get_forest_cover_area_type_state(state_feature, forest_classification)
        combined = combined.merge(result)

    selectors = ['NAME'] + [fc['name'] for fc in forest_classification]
    filename = f'forest_cover_area_type_{region_label}'

    state_task = ee.batch.Export.table.toDrive(
        collection=combined,
        description=filename,
        folder='GEE_exports',
        fileNamePrefix=filename,
        fileFormat='CSV',
        selectors=selectors
    )
    state_task.start()
    print(f'✅ Single export task submitted: {filename}')
    return state_task


# ── SECTION 7A: Forest Area by Bin and GLC Forest Type with Hansen tree cover — US States  2000 ─────────────

def get_forest_area_bin_type_state(state_feature, bins, forest_classification):
    """
    For one state feature, compute forest area (Mha) per GLC forest type
    for each canopy cover bin — both masks applied simultaneously at pixel level.
    Returns a GEE FeatureCollection — one Feature with one column per (class x bin).
    """
    class_images = []
    for fc in forest_classification:
        for i in range(len(bins) - 1):
            forest_mask_bin = (
                treecover2000_masked.gte(bins[i])
                .And(treecover2000_masked.lt(bins[i+1]))
                .selfMask()
                .updateMask(datamask.eq(1))
            )
            class_mask_bin = glc_2000.eq(fc['code']).And(forest_mask_bin)
            class_area_bin = class_mask_bin.multiply(ee.Image.pixelArea().divide(1e10)).rename(f"{fc['name']} - {bins[i]}-{bins[i+1]}")
            class_images.append(class_area_bin)

    multi_band_image = ee.Image.cat(class_images)

    region_area = multi_band_image.reduceRegions(
        collection=ee.FeatureCollection([state_feature]),
        reducer=ee.Reducer.sum(),
        scale=30
    )
    return region_area


def export_forest_area_bin_type_all_states(selected_states, bins, forest_classification, region_label='all_states'):
    """
    Loop over all states, build one combined FeatureCollection,
    and submit a single export task to Drive.
    Output columns: NAME + one column per (GLC forest class x bin)
    """
    tiger_states = ee.FeatureCollection('TIGER/2018/States') \
                     .filter(ee.Filter.inList('NAME', selected_states))
    state_list = tiger_states.toList(tiger_states.size())
    n = tiger_states.size().getInfo()

    combined = ee.FeatureCollection([])
    for i in range(n):
        state_feature = ee.Feature(state_list.get(i))
        result = get_forest_area_bin_type_state(state_feature, bins, forest_classification)
        combined = combined.merge(result)

    selectors = ['NAME'] + [f"{fc['name']} - {bins[i]}-{bins[i+1]}"
                            for fc in forest_classification
                            for i in range(len(bins) - 1)]
    filename = f'forest_area_bin_type_{region_label}'

    state_task = ee.batch.Export.table.toDrive(
        collection=combined,
        description=filename,
        folder='GEE_exports',
        fileNamePrefix=filename,
        fileFormat='CSV',
        selectors=selectors
    )
    state_task.start()
    print(f'✅ Single export task submitted: {filename}')
    return state_task

# ── SECTION 7B: Forest Area by Bin and GLC Forest Type with Treemap — US States 2016 ─────────────

def get_forest_area_bin_type_state_treemap_2016(state_feature, bins, forest_classification):

    GLC_FSC30D_annual = ee.ImageCollection('projects/sat-io/open-datasets/GLC-FCS30D/annual')
    glc_2016          = GLC_FSC30D_annual.mosaic().select('b17')  # b17 = year 2016

    tree_map          = ee.ImageCollection('USFS/GTAC/TreeMap/v2016') \
                          .filterDate('2016', '2017').first()
    canopypct_treemap = tree_map.select('CANOPYPCT')

    class_images = []
    for fc in forest_classification:
        for i in range(len(bins) - 1):
            forest_mask_treemap_bin = (
                canopypct_treemap.gte(bins[i])
                .And(canopypct_treemap.lt(bins[i+1]))
                .selfMask()
            )
            class_mask_bin  = glc_2016.eq(fc['code']).And(forest_mask_treemap_bin)
            class_area_bin  = class_mask_bin.multiply(ee.Image.pixelArea().divide(1e10)) \
                                .rename(f"{fc['name']} - {bins[i]}-{bins[i+1]}")
            class_images.append(class_area_bin)

    multi_band_image = ee.Image.cat(class_images)

    region_area = multi_band_image.reduceRegions(
        collection=ee.FeatureCollection([state_feature]),
        reducer=ee.Reducer.sum(),
        scale=30
    )
    return region_area

# ── SECTION 7C: Forest Area by Bin and GLC Forest Type with Treemap — US States 2020 ─────────────

def get_forest_area_bin_type_state_treemap_2020(state_feature, bins, forest_classification):

    GLC_FSC30D_annual = ee.ImageCollection('projects/sat-io/open-datasets/GLC-FCS30D/annual')
    glc_2020          = GLC_FSC30D_annual.mosaic().select('b21')  # b21 = year 2020

    tree_map          = ee.ImageCollection('USFS/GTAC/TreeMap/v2020') \
                          .filterDate('2020', '2021').first()
    canopypct_treemap = tree_map.select('CANOPYPCT')

    class_images = []
    for fc in forest_classification:
        for i in range(len(bins) - 1):
            forest_mask_treemap_bin = (
                canopypct_treemap.gte(bins[i])
                .And(canopypct_treemap.lt(bins[i+1]))
                .selfMask()
            )
            class_mask_bin = glc_2020.eq(fc['code']).And(forest_mask_treemap_bin)
            class_area_bin = class_mask_bin.multiply(ee.Image.pixelArea().divide(1e10)) \
                               .rename(f"{fc['name']} - {bins[i]}-{bins[i+1]}")
            class_images.append(class_area_bin)

    multi_band_image = ee.Image.cat(class_images)

    region_area = multi_band_image.reduceRegions(
        collection=ee.FeatureCollection([state_feature]),
        reducer=ee.Reducer.sum(),
        scale=30
    )
    return region_area
    
# ── SECTION 7D: Forest Area by Bin and GLC Forest Type with Treemap — US States 2022 ─────────────

def get_forest_area_bin_type_state_treemap_2022(state_feature, bins, forest_classification):

    GLC_FSC30D_annual = ee.ImageCollection('projects/sat-io/open-datasets/GLC-FCS30D/annual')
    glc_2022          = GLC_FSC30D_annual.mosaic().select('b23')  # b23 = year 2022

    tree_map          = ee.ImageCollection('USFS/GTAC/TreeMap/v2022') \
                          .filterDate('2022', '2023').first()
    canopypct_treemap = tree_map.select('CANOPYPCT')

    class_images = []
    for fc in forest_classification:
        for i in range(len(bins) - 1):
            forest_mask_treemap_bin = (
                canopypct_treemap.gte(bins[i])
                .And(canopypct_treemap.lt(bins[i+1]))
                .selfMask()
            )
            class_mask_bin = glc_2022.eq(fc['code']).And(forest_mask_treemap_bin)
            class_area_bin = class_mask_bin.multiply(ee.Image.pixelArea().divide(1e10)) \
                               .rename(f"{fc['name']} - {bins[i]}-{bins[i+1]}")
            class_images.append(class_area_bin)

    multi_band_image = ee.Image.cat(class_images)

    region_area = multi_band_image.reduceRegions(
        collection=ee.FeatureCollection([state_feature]),
        reducer=ee.Reducer.sum(),
        scale=30
    )
    return region_area

# ── SECTION 7E: EXPORT the calcatuon from sections 7B, 7C, 7D ---------- US States 2022 ─────────────

def export_forest_area_bin_type_all_states_treemap(
    selected_states, 
    bins, 
    forest_classification, 
    get_forest_area_bin_type_state_treemap_year,  # ← no default — must come first
    region_label='all_states'                      # ← has default — comes last
):
    tiger_states = ee.FeatureCollection('TIGER/2018/States') \
                     .filter(ee.Filter.inList('NAME', selected_states))
    state_list = tiger_states.toList(tiger_states.size())
    n          = tiger_states.size().getInfo()

    combined = ee.FeatureCollection([])
    for i in range(n):
        state_feature = ee.Feature(state_list.get(i))
        result        = get_forest_area_bin_type_state_treemap_year(
                            state_feature, bins, forest_classification
                        )
        combined = combined.merge(result)

    selectors = ['NAME'] + [f"{fc['name']} - {bins[i]}-{bins[i+1]}"
                            for fc in forest_classification
                            for i in range(len(bins) - 1)]
    filename  = f'forest_area_bin_type_treemap_{region_label}'

    state_task = ee.batch.Export.table.toDrive(
        collection=combined,
        description=filename,
        folder='GEE_exports',
        fileNamePrefix=filename,
        fileFormat='CSV',
        selectors=selectors
    )
    state_task.start()
    print(f'✅ Single export task submitted: {filename}')
    return state_task


# ── SECTION 8: Forest Area by Bin and GLC Forest Type — Countries ─────────────

def get_forest_area_bin_type_country(country_feature, bins, forest_classification):
    """
    For one country feature, compute forest area (Mha) per GLC forest type
    for each canopy cover bin — both masks applied simultaneously at pixel level.
    Returns a GEE FeatureCollection — one Feature with one column per (class x bin).
    """
    class_images = []
    for fc in forest_classification:
        for i in range(len(bins) - 1):
            forest_mask_bin = (
                treecover2000_masked.gte(bins[i])
                .And(treecover2000_masked.lt(bins[i+1]))
                .selfMask()
                .updateMask(datamask.eq(1))
            )
            class_mask_bin = glc_2000.eq(fc['code']).And(forest_mask_bin)
            class_area_bin = class_mask_bin.multiply(ee.Image.pixelArea().divide(1e10)).rename(f"{fc['name']} - {bins[i]}-{bins[i+1]}")
            class_images.append(class_area_bin)

    multi_band_image = ee.Image.cat(class_images)

    region_area = multi_band_image.reduceRegions(
        collection=ee.FeatureCollection([country_feature]),
        reducer=ee.Reducer.sum(),
        scale=30
    )
    return region_area


def export_forest_area_bin_type_all_countries(selected_regions, bins, forest_classification, region_label='all_countries'):
    """
    Loop over all countries, build one combined FeatureCollection,
    and submit a single export task to Drive.
    Output columns: country_na + one column per (GLC forest class x bin)
    """
    all_countries = get_all_countries(selected_regions)
    lsib_fao = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017') \
                  .filter(ee.Filter.inList('country_na', all_countries))
    country_list = lsib_fao.toList(lsib_fao.size())
    n = lsib_fao.size().getInfo()

    combined = ee.FeatureCollection([])
    for i in range(n):
        country_feature = ee.Feature(country_list.get(i))
        result = get_forest_area_bin_type_country(country_feature, bins, forest_classification)
        combined = combined.merge(result)

    selectors = ['country_na'] + [f"{fc['name']} - {bins[i]}-{bins[i+1]}"
                                  for fc in forest_classification
                                  for i in range(len(bins) - 1)]
    filename = f'forest_area_bin_type_{region_label}'

    country_task = ee.batch.Export.table.toDrive(
        collection=combined,
        description=filename,
        folder='GEE_exports',
        fileNamePrefix=filename,
        fileFormat='CSV',
        selectors=selectors
    )
    country_task.start()
    print(f'✅ Single export task submitted: {filename}')
    return country_task



# ── SECTION 9: Total GLC Forest Area — US States ──────────────────────────────

def get_glc_total_forest_area_state(state_feature):
    """
    For one state feature, compute total GLC forest area (Mha)
    summing all forest classes 51-92.
    Returns a GEE FeatureCollection — one Feature with total area.
    """
    area_image = glc_2000_forest.multiply(ee.Image.pixelArea().divide(1e10))

    region_area = area_image.reduceRegions(
        collection=ee.FeatureCollection([state_feature]),
        reducer=ee.Reducer.sum(),
        scale=30
    )
    return region_area


def export_glc_total_forest_area_all_states(selected_states, region_label='all_states'):
    """
    Loop over all states, build one combined FeatureCollection,
    and submit a single export task to Drive.
    Output columns: NAME, sum (total GLC forest area in Mha)
    """
    tiger_states = ee.FeatureCollection('TIGER/2018/States') \
                     .filter(ee.Filter.inList('NAME', selected_states))
    state_list = tiger_states.toList(tiger_states.size())
    n = tiger_states.size().getInfo()

    combined = ee.FeatureCollection([])
    for i in range(n):
        state_feature = ee.Feature(state_list.get(i))
        result = get_glc_total_forest_area_state(state_feature)
        combined = combined.merge(result)

    filename = f'glc_total_forest_area_{region_label}'

    task = ee.batch.Export.table.toDrive(
        collection=combined,
        description=filename,
        folder='GEE_exports',
        fileNamePrefix=filename,
        fileFormat='CSV',
        selectors=['NAME', 'sum']
    )
    task.start()
    print(f'✅ Single export task submitted: {filename}')
    return task


# ── SECTION 10: Total GLC Forest Area — Countries ─────────────────────────────

def get_glc_total_forest_area_country(country_feature):
    """
    For one country feature, compute total GLC forest area (Mha)
    summing all forest classes 51-92.
    Returns a GEE FeatureCollection — one Feature with total area.
    """
    area_image = glc_2000_forest.multiply(ee.Image.pixelArea().divide(1e10))

    region_area = area_image.reduceRegions(
        collection=ee.FeatureCollection([country_feature]),
        reducer=ee.Reducer.sum(),
        scale=30
    )
    return region_area


def export_glc_total_forest_area_all_countries(selected_regions, region_label='all_countries'):
    """
    Loop over all countries, build one combined FeatureCollection,
    and submit a single export task to Drive.
    Output columns: country_na, sum (total GLC forest area in Mha)
    """
    all_countries = get_all_countries(selected_regions)
    lsib_fao = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017') \
                  .filter(ee.Filter.inList('country_na', all_countries))
    country_list = lsib_fao.toList(lsib_fao.size())
    n = lsib_fao.size().getInfo()

    combined = ee.FeatureCollection([])
    for i in range(n):
        country_feature = ee.Feature(country_list.get(i))
        result = get_glc_total_forest_area_country(country_feature)
        combined = combined.merge(result)

    filename = f'glc_total_forest_area_{region_label}'

    task = ee.batch.Export.table.toDrive(
        collection=combined,
        description=filename,
        folder='GEE_exports',
        fileNamePrefix=filename,
        fileFormat='CSV',
        selectors=['country_na', 'sum']
    )
    task.start()
    print(f'✅ Single export task submitted: {filename}')
    return task


# ── SECTION 11: GEE export CSV files from Drive to the GitHub  ──────────────────────────────


def copy_gee_exports_to_repo(filenames, gee_folder, data_folder):
    """
    Copy GEE export CSV files from Drive to the GitHub repo data folder.
    Automatically renames standard GEE columns to clean names.
    """
    import shutil
    import os
    import pandas as pd

    os.makedirs(data_folder, exist_ok=True)

    column_rename = {
        'NAME':       'state',
        'country_na': 'country',
        'sum':        'area_Mha',
    }

    for f in filenames:
        src = gee_folder + f
        dst = data_folder + f

        df = pd.read_csv(src)

        # only rename columns that actually exist in this file
        rename_map = {k: v for k, v in column_rename.items() if k in df.columns}
        if rename_map:
            df.rename(columns=rename_map, inplace=True)

        df.to_csv(dst, index=False)
        print(f'✅ Copied and cleaned {f}')

# ── SECTION 12: Compute weighted mean canopy cover and std per GLC forest type  ──────────────────────────────

def compute_forest_type_composition(df, excluded_bins=None):
    import pandas as pd
    """
    Compute weighted mean canopy cover and std per GLC forest type.

    Input:
        df: wide dataframe loaded from 'forest_area_bin_type_{region_label}.csv'
            produced by the following pipeline:
                1. export_forest_area_bin_type_all_states() — GEE export
                2. copy_gee_exports_to_repo() — copy from Drive to repo

    Parameters:
        df:             wide dataframe (state | glc_class - bin columns)
        excluded_bins:  list of bins to exclude below the justified threshold.
                        threshold is region-specific — determine it by comparing
                        Hansen forest area against FAO statistics per region.
                        Examples:
                            US states:    excluded_bins=['10-20']          (threshold = 20%)
                            Global:       excluded_bins=['10-20', '20-30'] (threshold = 30%)
                            Tropical:     excluded_bins=['10-20', '20-30', '30-40'] (threshold = 40%)

    Returns:
        forest_type_stats:  one row per GLC class with
                            weighted_mean_canopy, weighted_std_canopy, total_area_Mha
        composition:        full distribution — glc_class | bin | area_Mha | bin_mid
    """
    if excluded_bins is None:
        raise ValueError(
            "excluded_bins must be specified — threshold is region-specific. "
            "Example: excluded_bins=['10-20'] for US (20%), ['10-20','20-30'] for global (30%)"
        )

    # Step 1 — melt to long format
    df_long = df.melt(id_vars='state', var_name='glc_bin', value_name='area_Mha')

    # Step 2 — split glc_bin into glc_class and bin
    df_long[['glc_class', 'bin']] = df_long['glc_bin'].str.split(' - ', expand=True)
    df_long = df_long.drop(columns='glc_bin')

    # Step 3 — filter excluded bins
    df_filtered = df_long[~df_long['bin'].isin(excluded_bins)]

    # Step 4 — aggregate across states
    composition = df_filtered.groupby(['glc_class', 'bin'])['area_Mha'].sum().reset_index()

    # Step 5 — bin midpoint
    composition['bin_mid'] = composition['bin'].apply(
        lambda x: (int(x.split('-')[0]) + int(x.split('-')[1])) / 2
    )

    # Step 6 — weighted mean and std per forest type
    def weighted_mean(group):
        return (group['bin_mid'] * group['area_Mha']).sum() / group['area_Mha'].sum()

    def weighted_std(group):
        mean = weighted_mean(group)
        variance = ((group['bin_mid'] - mean) ** 2 * group['area_Mha']).sum() / group['area_Mha'].sum()
        return variance ** 0.5

    forest_type_stats = composition.groupby('glc_class').apply(
        lambda g: pd.Series({
            'weighted_mean_canopy': weighted_mean(g),
            'weighted_std_canopy':  weighted_std(g),
            'total_area_Mha':       g['area_Mha'].sum()
        })
    ).reset_index()

    # Drop classes with no data
    forest_type_stats = forest_type_stats.dropna(subset=['weighted_mean_canopy'])

    return forest_type_stats, composition
