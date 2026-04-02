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


def export_forest_area(selected_regions, thresholds):
    """
    Merge all thresholds into one FeatureCollection and
    submit a single export task to Google Drive.
    Output columns: country, threshold, area_Mha
    """
    combined = ee.FeatureCollection([])

    for threshold in thresholds:
        fc = prepare_forest_collection(selected_regions, threshold)
        combined = combined.merge(fc)

    task = ee.batch.Export.table.toDrive(
        collection=combined,
        description='forest_area_all_thresholds',
        folder='GEE_exports',
        fileNamePrefix='forest_area_all_thresholds',
        fileFormat='CSV',
        selectors=['country_na', 'threshold', 'sum']
    )
    task.start()
    print('✅ Single export task submitted: forest_area_all_thresholds')
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


def export_states_forest_area(selected_states, thresholds):
    """
    Merge all thresholds into one FeatureCollection and
    submit a single export task to Google Drive.
    Output columns: state, threshold, area_Mha
    """
    combined = ee.FeatureCollection([])

    for threshold in thresholds:
        fc = prepare_states_forest_collection(selected_states, threshold)
        combined = combined.merge(fc)

    task = ee.batch.Export.table.toDrive(
        collection=combined,
        description='states_forest_area_all_thresholds',
        folder='GEE_exports',
        fileNamePrefix='states_forest_area_all_thresholds',
        fileFormat='CSV',
        selectors=['NAME', 'threshold', 'sum']
    )
    task.start()
    print('✅ Single export task submitted: states_forest_area_all_thresholds')
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


def export_forest_cover_bins_all_countries(selected_regions, bins):
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
        fc = get_forest_cover_bins_one_country(country_feature, bins)
        combined = combined.merge(fc)

    task = ee.batch.Export.table.toDrive(
        collection=combined,
        description='forest_cover_bins_all_countries',
        folder='GEE_exports',
        fileNamePrefix='forest_cover_bins_all_countries',
        fileFormat='CSV',
        selectors=['country_na', 'bin', 'sum']
    )
    task.start()
    print('✅ Single export task submitted: forest_cover_bins_all_countries')
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


def export_forest_cover_bins_all_states(selected_states, bins):
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
        fc = get_forest_cover_bins_one_state(state_feature, bins)
        combined = combined.merge(fc)

    task = ee.batch.Export.table.toDrive(
        collection=combined,
        description='forest_cover_bins_all_states',
        folder='GEE_exports',
        fileNamePrefix='forest_cover_bins_all_states',
        fileFormat='CSV',
        selectors=['NAME', 'bin', 'sum']
    )
    task.start()
    print('✅ Single export task submitted: forest_cover_bins_all_states')
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


def export_forest_cover_area_type_all_countries(selected_regions, forest_classification):
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
        fc = get_forest_cover_area_type_country(country_feature, forest_classification)
        combined = combined.merge(fc)

    selectors = ['country_na'] + [fc['name'] for fc in forest_classification]

    country_task = ee.batch.Export.table.toDrive(
        collection=combined,
        description='forest_cover_area_type_all_countries',
        folder='GEE_exports',
        fileNamePrefix='forest_cover_area_type_all_countries',
        fileFormat='CSV',
        selectors=selectors
    )
    country_task.start()
    print('✅ Single export task submitted: forest_cover_area_type_all_countries')
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


def export_forest_cover_area_type_all_states(selected_states, forest_classification):
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
        fc = get_forest_cover_area_type_state(state_feature, forest_classification)
        combined = combined.merge(fc)

    selectors = ['NAME'] + [fc['name'] for fc in forest_classification]

    state_task = ee.batch.Export.table.toDrive(
        collection=combined,
        description='forest_cover_area_type_all_states',
        folder='GEE_exports',
        fileNamePrefix='forest_cover_area_type_all_states',
        fileFormat='CSV',
        selectors=selectors
    )
    state_task.start()
    print('✅ Single export task submitted: forest_cover_area_type_all_states')
    return state_task
