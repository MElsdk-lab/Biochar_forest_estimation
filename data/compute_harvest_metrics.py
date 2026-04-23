"""
═══════════════════════════════════════════════════════════════════════════════
 compute_metrics.py
═══════════════════════════════════════════════════════════════════════════════

Universal metrics and export function for all harvest filter approaches.

Works for:
  - Harvest detection filters (A1, A2, B1, B1a, LT1, LT2, LT3)
    → binary mask only → area output

  - Rotation models (A3, A4, A5, A6)
    → mask + annual_fraction → area + annual residue output

  - Any filter + TreeMap (US only)
    → mask + TreeMap volume/biomass → volume + residue output

Exports as GEE FeatureCollection to Google Drive — no getInfo() calls.
═══════════════════════════════════════════════════════════════════════════════
"""

import ee


# Constants
PIXEL_AREA_CONVERSION = 1e4          # m² → ha
VOL_FT3_PER_ACRE_TO_M3_HA  = 0.0699  # ft³/acre → m³/ha
BIO_TONS_PER_ACRE_TO_MG_HA = 2.2417  # tons/acre → Mg/ha (ODT/ha)
BRANCH_FRACTION            = 0.275   # branches + tops / total AGB


def compute_metrics_export(mask,
                           region_geom,
                           region_name,
                           year,
                           filter_name,
                           treemap_vol=None,
                           treemap_bio=None,
                           annual_fraction=None,
                           extra_props=None,
                           export_folder='GEE_exports'):
    """
    Universal metrics function — computes area and optionally
    volume/residue for any harvest filter mask, then exports
    as GEE FeatureCollection to Drive.

    Parameters
    ----------
    mask : ee.Image
        Binary mask of detected pixels.
    region_geom : ee.Geometry
        Region to reduce over.
    region_name : str
        Name of region (used in output + filename).
    year : int or str
        Year or year range (used in output + filename).
    filter_name : str
        Filter identifier (used in output + filename).
    treemap_vol : ee.Image, optional
        TreeMap VOLCFNET_L image in ft³/acre. If provided, volume is computed.
    treemap_bio : ee.Image, optional
        TreeMap DRYBIO_L image in tons/acre. If provided, residue is computed.
    annual_fraction : ee.Image, optional
        1/rotation image. If provided, residue is multiplied by annual fraction.
    extra_props : dict, optional
        Additional properties to store in the feature (e.g. mag_threshold).
    export_folder : str
        Google Drive folder name.

    Returns
    -------
    ee.batch.Task
        The started export task.
    """

    # ── Pixel area in ha ──
    pixel_area_ha = (
        ee.Image.pixelArea()
        .divide(PIXEL_AREA_CONVERSION)
        .updateMask(mask)
    )

    # ── Build band stack ──
    bands = [pixel_area_ha.rename('area_ha')]

    if treemap_vol is not None:
        vol_m3_ha = (
            treemap_vol
            .multiply(VOL_FT3_PER_ACRE_TO_M3_HA)
            .updateMask(mask)
        )
        bands.append(vol_m3_ha.rename('vol_m3_ha'))

    if treemap_bio is not None:
        residue_ODT_ha = (
            treemap_bio
            .multiply(BIO_TONS_PER_ACRE_TO_MG_HA)
            .multiply(BRANCH_FRACTION)
            .updateMask(mask)
        )
        if annual_fraction is not None:
            residue_ODT_ha = residue_ODT_ha.multiply(annual_fraction)
        bands.append(residue_ODT_ha.rename('residue_ODT_ha'))

    # ── Stack bands ──
    combined = bands[0]
    for b in bands[1:]:
        combined = combined.addBands(b)

    # ── Reduce — sum + mean in one pass ──
    stats = combined.reduceRegion(
        reducer=ee.Reducer.sum().combine(
            ee.Reducer.mean(),
            sharedInputs=False
        ),
        geometry=region_geom,
        scale=30,
        maxPixels=1e13
    )

    # ── Build feature properties ──
    feature_props = {
        'region':      region_name,
        'year':        year,
        'filter_type': filter_name,
        'area_ha':     stats.get('area_ha_sum'),
    }

    if treemap_vol is not None:
        feature_props['mean_vol_m3_ha'] = stats.get('vol_m3_ha_mean')
        feature_props['total_vol_m3']   = stats.get('vol_m3_ha_sum')

    if treemap_bio is not None:
        feature_props['mean_residue_ODT_ha'] = stats.get('residue_ODT_ha_mean')
        feature_props['total_residue_ODT']   = stats.get('residue_ODT_ha_sum')

    # Merge extra props (e.g. mag_threshold, recovery_window)
    if extra_props:
        feature_props.update(extra_props)

    feature = ee.Feature(None, feature_props)

    # ── Export as FeatureCollection to Drive ──
    fc = ee.FeatureCollection([feature])

    filename = f'{filter_name}_{region_name}_{year}'

    task = ee.batch.Export.table.toDrive(
        collection     = fc,
        description    = filename,
        folder         = export_folder,
        fileNamePrefix = filename,
        fileFormat     = 'CSV'
    )

    task.start()
    print(f'🚀 {filter_name} | {region_name} | {year}')

    return task


# ════════════════════════════════════════════════════════════════════════════════
# BATCH HELPERS — run multiple approaches at once
# ════════════════════════════════════════════════════════════════════════════════

def batch_run_group_A(states_dict, years, treemap_by_year, rotation_cycle,
                      harvest_filters, export_folder='GEE_exports'):
    """
    Run all Group A approaches (A1–A6) for multiple states × years.

    Parameters
    ----------
    states_dict : dict
        {state_name: state_geom}
    years : list of int
        Years to process (must be in treemap_by_year keys).
    treemap_by_year : dict
        {year: {'vol': ee.Image, 'bio': ee.Image}}
    rotation_cycle : list
        Rotation years for Lesiv classes [11, 20, 31, 32, 40, 53].
    harvest_filters : module
        The imported harvest_filters module.
    """
    tasks = []

    for year in years:

        if year not in treemap_by_year:
            print(f'⚠ TreeMap not available for {year}, skipping')
            continue

        t_vol = treemap_by_year[year]['vol']
        t_bio = treemap_by_year[year]['bio']

        for region_name, region_geom in states_dict.items():

            # A1
            mask = harvest_filters.harvest_filter_A1_H_S(region_geom, year)
            tasks.append(compute_metrics_export(
                mask, region_geom, region_name, year,
                'A1_H_S', t_vol, t_bio,
                export_folder=export_folder
            ))

            # A2
            mask = harvest_filters.harvest_filter_A2_H_S_L(region_geom, year)
            tasks.append(compute_metrics_export(
                mask, region_geom, region_name, year,
                'A2_H_S_L', t_vol, t_bio,
                export_folder=export_folder
            ))

            # A3
            mask, frac = harvest_filters.harvest_filter_A3_L_only(
                region_geom, year, rotation_cycle
            )
            tasks.append(compute_metrics_export(
                mask, region_geom, region_name, year,
                'A3_L_rotation', t_vol, t_bio,
                annual_fraction=frac,
                export_folder=export_folder
            ))

            # A4
            mask, frac = harvest_filters.harvest_filter_A4_L_not_S(
                region_geom, year, rotation_cycle
            )
            tasks.append(compute_metrics_export(
                mask, region_geom, region_name, year,
                'A4_L_not_S', t_vol, t_bio,
                annual_fraction=frac,
                export_folder=export_folder
            ))

            # A5
            mask, frac = harvest_filters.harvest_filter_A5_L_H_pre2015(
                region_geom, year, rotation_cycle
            )
            tasks.append(compute_metrics_export(
                mask, region_geom, region_name, year,
                'A5_L_H_pre2015', t_vol, t_bio,
                annual_fraction=frac,
                export_folder=export_folder
            ))

            # A6
            mask, frac = harvest_filters.harvest_filter_A6_L_not_H(
                region_geom, year, rotation_cycle
            )
            tasks.append(compute_metrics_export(
                mask, region_geom, region_name, year,
                'A6_L_not_H', t_vol, t_bio,
                annual_fraction=frac,
                export_folder=export_folder
            ))

    return tasks


def batch_run_B1(states_dict, harvest_filters,
                 treemap_vol=None, treemap_bio=None,
                 adaptive=True, export_folder='GEE_exports'):
    """
    Run B1 GLC thinning detection for all states.
    Exports one row per transition year + one combined row per state.

    If adaptive=True uses B1_adaptive (2002–2020).
    If adaptive=False uses B1 fixed (2002–2014).
    """
    tasks = []

    for region_name, region_geom in states_dict.items():

        if adaptive:
            detections, combined = harvest_filters.harvest_filter_B1_GLC_thinning_adaptive(
                region_geom, region_name
            )
            # Per-transition-year features
            for transition_year, entry in detections.items():
                tasks.append(compute_metrics_export(
                    entry['mask'], region_geom, region_name,
                    transition_year, 'B1a_GLC_thinning',
                    treemap_vol, treemap_bio,
                    extra_props={'recovery_window_yrs': entry['recovery_window']},
                    export_folder=export_folder
                ))
            # Combined
            tasks.append(compute_metrics_export(
                combined, region_geom, region_name,
                'all_2002_2020', 'B1a_GLC_thinning_combined',
                treemap_vol, treemap_bio,
                export_folder=export_folder
            ))

        else:
            detections, combined = harvest_filters.harvest_filter_B1_GLC_thinning(
                region_geom, region_name
            )
            for transition_year, mask in detections.items():
                tasks.append(compute_metrics_export(
                    mask, region_geom, region_name,
                    transition_year, 'B1_GLC_thinning',
                    treemap_vol, treemap_bio,
                    export_folder=export_folder
                ))
            tasks.append(compute_metrics_export(
                combined, region_geom, region_name,
                'all_2002_2014', 'B1_GLC_thinning_combined',
                treemap_vol, treemap_bio,
                export_folder=export_folder
            ))

    return tasks


def batch_run_LT(states_dict, harvest_filters,
                 mag_thresholds=[0.1, 0.3, 0.5],
                 indices=['NBR', 'SWIR2'],
                 start_year=2001,
                 end_year=2022,
                 export_folder='GEE_exports'):
    """
    Run LandTrendr approaches LT1, LT2, LT3 for all states × indices × thresholds.
    """
    tasks = []

    lt_functions = {
        'LT1_alone':         harvest_filters.harvest_filter_LT1_alone,
        'LT2_keep_logging':  harvest_filters.harvest_filter_LT2_keep_logging,
        'LT3_pure_thinning': harvest_filters.harvest_filter_LT3_pure_thinning,
    }

    for region_name, region_geom in states_dict.items():
        for index_name in indices:
            for mag in mag_thresholds:
                for lt_name, lt_func in lt_functions.items():
                    mask, year_img = lt_func(
                        region_geom, region_name,
                        mag_threshold=mag,
                        start_year=start_year,
                        end_year=end_year,
                        index_name=index_name
                    )
                    full_name = f'{lt_name}_{index_name}_mag{int(mag*100)}'
                    tasks.append(compute_metrics_export(
                        mask, region_geom, region_name,
                        f'all_{start_year}_{end_year}',
                        full_name,
                        extra_props={
                            'index':         index_name,
                            'mag_threshold': mag,
                        },
                        export_folder=export_folder
                    ))

    return tasks
