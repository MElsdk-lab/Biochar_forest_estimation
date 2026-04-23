"""
═══════════════════════════════════════════════════════════════════════════════
 harvest_filters.py
═══════════════════════════════════════════════════════════════════════════════

Harvest filter functions for global biochar feedstock methodology — Step 2.

Approaches:
  A1   Hansen × Sims                              (upper bound)
  A2   Hansen × Sims × Lesiv                      (✅ validated Approach 1)
  A3   Lesiv ÷ rotation                           (full managed stock)
  A4   Lesiv ÷ rotation × NOT Sims                (thinning gap)
  A5   Lesiv × Hansen pre-2015                    (historical detection)
  A6   Lesiv × NOT Hansen (any year)              (never detected)
  B1   GLC closed → open → closed, 7yr window     (structural thinning)
  B1a  GLC closed → open → closed, adaptive       (structural thinning)
  LT1  LandTrendr alone                           (spectral sensitivity)
  LT2  LandTrendr × NOT (Sims non-logging)        (keep logging, remove noise)
  LT3  LandTrendr × NOT (Sims any class)          (pure thinning signal)

Datasets injected at runtime:
  lossyear               — Hansen GFC lossyear band (0–24)
  drivers_class          — Sims et al. 2025 class band
  logging_mask           — Sims class 4 binary
  lesiv_managed_30m      — Lesiv managed forest 20/31/32 binary
  fml                    — Lesiv raw remap-capable image
  GLC_FSC30D_annual      — GLC FCS30D annual ImageCollection
  forest_union_mask      — union GLC forest mask 2000–2022 (band 'forest')

Sims classes:
  1 = Permanent agriculture          2 = Hard commodities (mining)
  3 = Shifting cultivation           4 = Logging
  5 = Wildfires                      6 = Settlements and infrastructure
  7 = Other natural disturbances
═══════════════════════════════════════════════════════════════════════════════
"""

import ee
from ltgee import LandTrendr, LtCollection


# ════════════════════════════════════════════════════════════════════════════════
# GROUP A — HANSEN × SIMS × LESIV COMBINATIONS
# ════════════════════════════════════════════════════════════════════════════════

def harvest_filter_A1_H_S(state_geom, year):
    """A1 — Hansen × Sims logging. No Lesiv. Upper bound."""
    y_code = year - 2000
    hansen = lossyear.eq(y_code)

    mask = (
        hansen
        .And(logging_mask)
        .selfMask()
        .clip(state_geom)
    )
    return mask


def harvest_filter_A2_H_S_L(state_geom, year):
    """A2 — Hansen × Sims × Lesiv. ✅ Validated Oregon 102%."""
    y_code = year - 2000
    hansen = lossyear.eq(y_code)

    mask = (
        hansen
        .And(logging_mask)
        .And(lesiv_managed_30m)
        .selfMask()
        .clip(state_geom)
    )
    return mask


# ════════════════════════════════════════════════════════════════════════════════
# GROUP A — LESIV ROTATION MODELS
# ════════════════════════════════════════════════════════════════════════════════

def _build_rotation_image(rotation_cycle):
    """Build rotation image from Lesiv class codes [11,20,31,32,40,53]."""
    return fml.remap(
        [11, 20, 31, 32, 40, 53],
        rotation_cycle
    )


def _glc_forest_year_before(year):
    """GLC forest mask for the year BEFORE harvest."""
    y_band_before = year - 2000
    glc_before = GLC_FSC30D_annual.mosaic().select(f'b{y_band_before}')
    return glc_before.gte(51).And(glc_before.lte(92)).rename('glc_forest')


def harvest_filter_A3_L_only(state_geom, year, rotation_cycle):
    """A3 — Lesiv managed × GLC forest year before. Full stock."""
    glc_forest = _glc_forest_year_before(year)
    rotation_image = _build_rotation_image(rotation_cycle)

    managed_mask = (
        lesiv_managed_30m
        .And(glc_forest)
        .selfMask()
        .clip(state_geom)
    )

    annual_fraction = ee.Image(1).divide(
        rotation_image.updateMask(managed_mask)
    )

    return managed_mask, annual_fraction


def harvest_filter_A4_L_not_S(state_geom, year, rotation_cycle):
    """A4 — Lesiv × GLC × NOT Sims. Thinning gap."""
    glc_forest = _glc_forest_year_before(year)
    rotation_image = _build_rotation_image(rotation_cycle)

    managed_mask = (
        lesiv_managed_30m
        .And(glc_forest)
        .And(logging_mask.unmask(0).Not())
        .selfMask()
        .clip(state_geom)
    )

    annual_fraction = ee.Image(1).divide(
        rotation_image.updateMask(managed_mask)
    )

    return managed_mask, annual_fraction


def harvest_filter_A5_L_H_pre2015(state_geom, year, rotation_cycle):
    """A5 — Lesiv × GLC × Hansen loss 2001-2014. Historical."""
    glc_forest = _glc_forest_year_before(year)
    rotation_image = _build_rotation_image(rotation_cycle)

    hansen_pre_2015 = lossyear.gt(0).And(lossyear.lt(15))

    managed_mask = (
        lesiv_managed_30m
        .And(glc_forest)
        .And(hansen_pre_2015)
        .selfMask()
        .clip(state_geom)
    )

    annual_fraction = ee.Image(1).divide(
        rotation_image.updateMask(managed_mask)
    )

    return managed_mask, annual_fraction


def harvest_filter_A6_L_not_H(state_geom, year, rotation_cycle):
    """A6 — Lesiv × GLC × NOT Hansen (any year). Never-detected forest."""
    glc_forest = _glc_forest_year_before(year)
    rotation_image = _build_rotation_image(rotation_cycle)

    hansen_any_loss = lossyear.gt(0)

    managed_mask = (
        lesiv_managed_30m
        .And(glc_forest)
        .And(hansen_any_loss.unmask(0).Not())
        .selfMask()
        .clip(state_geom)
    )

    annual_fraction = ee.Image(1).divide(
        rotation_image.updateMask(managed_mask)
    )

    return managed_mask, annual_fraction


# ════════════════════════════════════════════════════════════════════════════════
# GROUP B — GLC CLOSED → OPEN → CLOSED STRUCTURAL THINNING
# ════════════════════════════════════════════════════════════════════════════════

def _build_glc_binary_annual():
    """Build annual GLC binary masks — closed vs open forest — 2000-2022."""
    closed_classes = [52, 62, 72, 82, 92]
    open_classes   = [51, 61, 71, 81, 91]

    glc_annual = {}
    for year in range(2000, 2023):
        i = year - 2000
        band = GLC_FSC30D_annual.mosaic().select(f'b{i + 1}')
        glc_annual[year] = {
            'closed': band.remap(closed_classes, [1]*5).eq(1).rename('closed'),
            'open':   band.remap(open_classes,   [1]*5).eq(1).rename('open'),
        }

    return glc_annual


def harvest_filter_B1_GLC_thinning(region_geom, region_name):
    """B1 — GLC closed → open → closed, fixed 7-year recovery window."""
    glc_annual = _build_glc_binary_annual()

    baseline_closed = (
        glc_annual[2000]['closed']
        .And(glc_annual[2001]['closed'])
    )

    thinning_detections = {}

    for transition_year in range(2002, 2015):
        stable_closed = glc_annual[transition_year - 1]['closed']
        becomes_open  = glc_annual[transition_year]['open']

        recovery = glc_annual[transition_year + 1]['closed']
        for offset in range(2, 8):
            recovery = recovery.Or(glc_annual[transition_year + offset]['closed'])

        thinning_mask = (
            baseline_closed
            .And(stable_closed)
            .And(becomes_open)
            .And(recovery)
            .selfMask()
            .clip(region_geom)
        )

        thinning_detections[transition_year] = thinning_mask

    combined_thinning = ee.ImageCollection(
        list(thinning_detections.values())
    ).max().selfMask()

    return thinning_detections, combined_thinning


def harvest_filter_B1_GLC_thinning_adaptive(region_geom, region_name):
    """B1a — GLC closed → open → closed, adaptive recovery window."""
    glc_annual = _build_glc_binary_annual()

    baseline_closed = (
        glc_annual[2000]['closed']
        .And(glc_annual[2001]['closed'])
    )

    thinning_detections = {}

    for transition_year in range(2002, 2021):
        stable_closed = glc_annual[transition_year - 1]['closed']
        becomes_open  = glc_annual[transition_year]['open']

        max_recovery_year = min(transition_year + 7, 2022)
        recovery_years = list(range(transition_year + 1, max_recovery_year + 1))
        recovery_window_length = len(recovery_years)

        recovery = glc_annual[recovery_years[0]]['closed']
        for ry in recovery_years[1:]:
            recovery = recovery.Or(glc_annual[ry]['closed'])

        thinning_mask = (
            baseline_closed
            .And(stable_closed)
            .And(becomes_open)
            .And(recovery)
            .selfMask()
            .clip(region_geom)
        )

        thinning_detections[transition_year] = {
            'mask': thinning_mask,
            'recovery_window': recovery_window_length,
        }

    masks_only = [d['mask'] for d in thinning_detections.values()]
    combined_thinning = ee.ImageCollection(masks_only).max().selfMask()

    return thinning_detections, combined_thinning


# ════════════════════════════════════════════════════════════════════════════════
# GROUP LT — LANDTRENDR HELPERS (using lt-gee-py)
# ════════════════════════════════════════════════════════════════════════════════

TM_BAND_NAMES = ['B1', 'B2', 'B3', 'B4', 'B5', 'B7']


def _mask_landsat_sr(image):
    """Cloud + shadow + snow mask for Landsat Collection 2 SR."""
    qa = image.select('QA_PIXEL')
    cloud  = qa.bitwiseAnd(1 << 3).eq(0)
    shadow = qa.bitwiseAnd(1 << 4).eq(0)
    snow   = qa.bitwiseAnd(1 << 5).eq(0)
    return image.updateMask(cloud).updateMask(shadow).updateMask(snow)


def _prep_l5(image):
    """L5: rename to TM-equivalent bands, apply SR scaling."""
    scaled = (image.select(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B7'],
                           TM_BAND_NAMES)
              .multiply(0.0000275).add(-0.2)
              .multiply(10000).toUint16())
    return _mask_landsat_sr(image).addBands(scaled, overwrite=True).select(TM_BAND_NAMES)


def _prep_l89(image):
    """L8/L9: shift band numbers to match TM. SR_B2-B7 → B1-B5,B7."""
    scaled = (image.select(['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7'],
                           TM_BAND_NAMES)
              .multiply(0.0000275).add(-0.2)
              .multiply(10000).toUint16())
    return _mask_landsat_sr(image).addBands(scaled, overwrite=True).select(TM_BAND_NAMES)


def _build_annual_sr_composite(year, aoi):
    """
    Build annual 6-band TM-equivalent median composite.
    L5 (≤2012), L8 (2013-2021), L8+L9 (2022+).
    Hemisphere-aware window.
    """
    centroid = aoi.centroid(maxError=1)
    lat = ee.Number(centroid.coordinates().get(1))

    nh_start = ee.Date.fromYMD(year, 6, 1)
    nh_end   = ee.Date.fromYMD(year, 9, 30)
    sh_start = ee.Date.fromYMD(year, 12, 1)
    sh_end   = ee.Date.fromYMD(year + 1, 2, 28)

    start = ee.Date(ee.Algorithms.If(lat.gt(0), nh_start, sh_start))
    end   = ee.Date(ee.Algorithms.If(lat.gt(0), nh_end,   sh_end))

    if year <= 2012:
        col = (ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
               .filterDate(start, end).filterBounds(aoi).map(_prep_l5))
    elif year <= 2021:
        col = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
               .filterDate(start, end).filterBounds(aoi).map(_prep_l89))
    else:
        l8 = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
              .filterDate(start, end).filterBounds(aoi).map(_prep_l89))
        l9 = (ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
              .filterDate(start, end).filterBounds(aoi).map(_prep_l89))
        col = l8.merge(l9)

    dummy = (ee.Image([0, 0, 0, 0, 0, 0])
             .rename(TM_BAND_NAMES)
             .toUint16()
             .updateMask(ee.Image(0)))

    composite = ee.Image(ee.Algorithms.If(
        col.size().gt(0),
        col.median().select(TM_BAND_NAMES).toUint16(),
        dummy
    ))

    return composite.set('system:time_start',
                         ee.Date.fromYMD(year, 6, 1).millis())


def _build_sr_collection(aoi, start_year, end_year):
    """Build ee.ImageCollection of annual SR composites."""
    images = [_build_annual_sr_composite(y, aoi)
              for y in range(start_year, end_year + 1)]
    return ee.ImageCollection.fromImages(images)


def _run_landtrendr(sr_collection, index_name='NBR'):
    """
    Run LandTrendr via lt-gee-py.
    index_name: 'NBR' or 'B7' (SWIR2 in TM-equivalent naming)
    """
    lt_col = LtCollection(
        sr_collection = sr_collection,
        index         = index_name,
        ftv_list      = [index_name]
    )

    lt = LandTrendr(
        lt_collection = lt_col,
        run_params    = {
            "maxSegments":            6,
            "spikeThreshold":         0.9,
            "vertexCountOvershoot":   3,
            "preventOneYearRecovery": True,
            "recoveryThreshold":      0.25,
            "pvalThreshold":          0.05,
            "bestModelProportion":    0.75,
            "minObservationsNeeded":  6,
        }
    )

    return lt


def _get_change_mask(lt, start_year, end_year, mag_threshold):
    """
    Extract disturbance mask from LandTrendr result.
    mag_threshold in index × 1000 scale (200 = 0.2 NBR drop).
    """
    change_image = lt.get_change_map({
        'delta':  'loss',
        'sort':   'greatest',
        'years':  {'start': start_year, 'end': end_year},
        'mag':    {'value': mag_threshold, 'operator': '>'},
        'mmu':    {'value': 11},
    })

    disturbance_mask = change_image.select('mag').gt(0).selfMask()
    year_image       = change_image.select('yod')
    mag_image        = change_image.select('mag')

    return disturbance_mask, year_image, mag_image


# ════════════════════════════════════════════════════════════════════════════════
# GROUP LT — LANDTRENDR APPROACHES
# ════════════════════════════════════════════════════════════════════════════════

def harvest_filter_LT1_alone(region_geom, region_name,
                              mag_threshold=200,
                              start_year=2001,
                              end_year=2022,
                              index_name='NBR'):
    """
    LT1 — LandTrendr alone.
    Pure spectral disturbance, no driver or management filter.

    mag_threshold: NBR/SWIR2 drop × 1000
      200 = sensitive (thinning)
      300 = moderate
      500 = strict (clearcuts)
    index_name: 'NBR' or 'B7' (SWIR2)
    """
    sr_collection = _build_sr_collection(region_geom, start_year, end_year)
    lt = _run_landtrendr(sr_collection, index_name)
    disturbance_mask, year_image, mag_image = _get_change_mask(
        lt, start_year, end_year, mag_threshold
    )

    mask = (disturbance_mask
            .updateMask(forest_union_mask)
            .clip(region_geom))

    return mask, year_image


def harvest_filter_LT2_keep_logging(region_geom, region_name,
                                     mag_threshold=200,
                                     start_year=2001,
                                     end_year=2022,
                                     index_name='NBR'):
    """
    LT2 — LandTrendr × NOT (Hansen × Sims non-logging).
    Removes Sims 1,2,3,5,6,7 (agriculture, mining, fire, urban, etc.).
    KEEPS class 4 (logging).

    Captures thinning + clearcut + selective logging
    without fire/agriculture false positives.
    """
    sr_collection = _build_sr_collection(region_geom, start_year, end_year)
    lt = _run_landtrendr(sr_collection, index_name)
    disturbance_mask, year_image, mag_image = _get_change_mask(
        lt, start_year, end_year, mag_threshold
    )

    sims_non_logging = (
        drivers_class.eq(1)
        .Or(drivers_class.eq(2))
        .Or(drivers_class.eq(3))
        .Or(drivers_class.eq(5))
        .Or(drivers_class.eq(6))
        .Or(drivers_class.eq(7))
    )

    hansen_any_loss = lossyear.gt(0)
    exclude_mask = sims_non_logging.And(hansen_any_loss)

    mask = (disturbance_mask
            .And(exclude_mask.unmask(0).Not())
            .updateMask(forest_union_mask)
            .selfMask()
            .clip(region_geom))

    return mask, year_image


def harvest_filter_LT3_pure_thinning(region_geom, region_name,
                                      mag_threshold=200,
                                      start_year=2001,
                                      end_year=2022,
                                      index_name='NBR'):
    """
    LT3 — LandTrendr × NOT (Hansen × Sims any class 1-7).
    Removes ALL Sims-classified disturbance.
    Retains only spectral change NOT attributed to any Sims driver.

    Assumed to be pure thinning since Sims covers all known drivers.
    """
    sr_collection = _build_sr_collection(region_geom, start_year, end_year)
    lt = _run_landtrendr(sr_collection, index_name)
    disturbance_mask, year_image, mag_image = _get_change_mask(
        lt, start_year, end_year, mag_threshold
    )

    sims_any = drivers_class.gte(1).And(drivers_class.lte(7))
    hansen_any_loss = lossyear.gt(0)
    exclude_mask = sims_any.And(hansen_any_loss)

    mask = (disturbance_mask
            .And(exclude_mask.unmask(0).Not())
            .updateMask(forest_union_mask)
            .selfMask()
            .clip(region_geom))

    return mask, year_image
