"""
═══════════════════════════════════════════════════════════════════════════════
 harvest_filters.py — FINAL HYBRID VERSION
═══════════════════════════════════════════════════════════════════════════════

Hybrid masking approach — verified correct at scale=1000:
  - POSITIVE identity tracks (A1, A2): return FRACTIONAL masks (via reduceResolution mean)
  - NEGATION tracks (A4, A5, A6): return BINARY masks (selfMask)

Why hybrid is necessary:
  - Fractional approach fails for negation tracks because .unmask(0).Not()
    inflates NoData regions
  - Binary approach fails for sparse positive tracks (A1) because each 1km
    cell containing ANY 30m harvest pixel counts as full 100 ha (4x inflation)

Verified results at scale=1000 (Oregon 2022):
  A1 fractional:   70,725 ha   (matches 30m truth: 70,734 ha) ✓
  A4 binary:    5,267,635 ha   (matches inline manual test) ✓
  A6 binary:    2,246,501 ha   (matches inline manual test, A6 < A4) ✓

Datasets injected at runtime:
  hansen_2024            — Hansen GFC full image (with first_b30/40/50/70, last_b30/40/50/70)
  lossyear, drivers_class, logging_mask, lesiv_managed_30m, fml,
  GLC_FSC30D_annual, forest_union_mask
═══════════════════════════════════════════════════════════════════════════════
"""

import ee
from ltgee import LandTrendr, LtCollection


# Target output resolution (used for fractional aggregation)
TARGET_SCALE = 1000
DEFAULT_CRS  = 'EPSG:4326'


# ════════════════════════════════════════════════════════════════════════════════
# HELPER — Fractional 1km mask (for POSITIVE identity tracks only)
# ════════════════════════════════════════════════════════════════════════════════

def _to_fractional_1km(binary_mask, region_geom):
    """
    Convert a positive-identity binary mask to a fractional 1km mask.
    
    DO NOT use this for tracks containing .Not() / negation —
    NoData inflation breaks the result.
    """
    return (
        binary_mask.unmask(0)
        .reduceResolution(
            reducer=ee.Reducer.mean(),
            maxPixels=2000
        )
        .reproject(crs=DEFAULT_CRS, scale=TARGET_SCALE)
        .clip(region_geom)
    )


# ════════════════════════════════════════════════════════════════════════════════
# GROUP A — HANSEN × SIMS × LESIV (POSITIVE → FRACTIONAL)
# ════════════════════════════════════════════════════════════════════════════════

def harvest_filter_A1_H_S(state_geom, year):
    """A1 — Hansen × Sims logging. Fractional 1km mask."""
    y_code = year - 2000
    binary = lossyear.eq(y_code).And(logging_mask)
    return _to_fractional_1km(binary, state_geom)


def harvest_filter_A2_H_S_L(state_geom, year):
    """A2 — Hansen × Sims × Lesiv. Fractional 1km mask."""
    y_code = year - 2000
    binary = (
        lossyear.eq(y_code)
        .And(logging_mask)
        .And(lesiv_managed_30m)
    )
    return _to_fractional_1km(binary, state_geom)


# ════════════════════════════════════════════════════════════════════════════════
# GROUP A — LESIV ROTATION MODELS (NEGATION → BINARY + selfMask)
# ════════════════════════════════════════════════════════════════════════════════

def _build_rotation_image(rotation_cycle):
    """Build rotation image from Lesiv class codes [11,20,31,32,40,53]."""
    return fml.remap(
        [11, 20, 31, 32, 40, 53],
        rotation_cycle
    )


def _glc_forest_year_before(year):
    """GLC forest mask for the year BEFORE harvest at native resolution."""
    y_band_before = year - 2000
    glc_before = GLC_FSC30D_annual.mosaic().select(f'b{y_band_before}')
    return glc_before.gte(51).And(glc_before.lte(92)).rename('glc_forest')


def harvest_filter_A3_L_only(state_geom, year, rotation_cycle):
    """A3 — Lesiv managed × GLC forest. Binary mask + selfMask."""
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
    """A4 — Lesiv × GLC × NOT Sims. Binary mask + selfMask."""
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
    """A5 — Lesiv × GLC × Hansen pre-2015. Binary mask + selfMask."""
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
    """A6 — Lesiv × GLC × NOT Hansen. Binary mask + selfMask."""
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
# GROUP HT — HANSEN SPECTRAL THINNING (first→last delta, NEGATION → BINARY)
# ════════════════════════════════════════════════════════════════════════════════
#
# Uses Hansen GFC's pre-computed spectral composites (first_b30/40/50/70 and
# last_b30/40/50/70) to detect thinning as canopy reduction NOT captured by
# Hansen's lossyear (which detects only ≥50% canopy loss = clearcuts).
#
# Hansen Bands:
#   first_b30 = RED  | first_b40 = NIR  | first_b50 = SWIR1 | first_b70 = SWIR2
#   last_b30  = RED  | last_b40  = NIR  | last_b50  = SWIR1 | last_b70  = SWIR2
#
# Indices computed:
#   NBR   = (NIR - SWIR2) / (NIR + SWIR2)            scaled to integer × 1000
#   SWIR2 = SWIR2 band directly (rises after harvest) raw 0-255 scale
#
# Default thresholds:
#   delta_NBR > 150     →  ~0.15 NBR drop  →  light thinning detection
#   delta_SWIR2 > 25    →  significant SWIR2 rise → bare/dry biomass exposure
#
# All HT functions return BINARY masks (selfMask) at native 30m resolution.
# Use mask_type='binary' in compute_metrics_export.
# ════════════════════════════════════════════════════════════════════════════════


def _compute_hansen_delta(index_name='NBR'):
    """
    Compute first→last delta from Hansen pre-built composites.
    Larger delta = stronger spectral disturbance (greener → less green).
    
    For NBR: delta = first_NBR - last_NBR (positive = canopy lost)
    For SWIR2: delta = last_b70 - first_b70 (positive = soil exposed)
    """
    if index_name == 'NBR':
        # NBR = (NIR - SWIR2) / (NIR + SWIR2), scaled ×1000 for integer math
        first_nir   = hansen_2024.select('first_b40').toFloat()
        first_swir2 = hansen_2024.select('first_b70').toFloat()
        last_nir    = hansen_2024.select('last_b40').toFloat()
        last_swir2  = hansen_2024.select('last_b70').toFloat()
        
        first_nbr = (first_nir.subtract(first_swir2)
                     .divide(first_nir.add(first_swir2).max(1))
                     .multiply(1000))
        last_nbr  = (last_nir.subtract(last_swir2)
                     .divide(last_nir.add(last_swir2).max(1))
                     .multiply(1000))
        
        # Drop = decrease in NBR
        delta = first_nbr.subtract(last_nbr).rename('delta_NBR')
        
    elif index_name == 'SWIR2':
        # SWIR2 rises with harvest (exposed soil)
        first_swir2 = hansen_2024.select('first_b70').toFloat()
        last_swir2  = hansen_2024.select('last_b70').toFloat()
        delta = last_swir2.subtract(first_swir2).rename('delta_SWIR2')
        
    else:
        raise ValueError(f"index_name must be 'NBR' or 'SWIR2', got '{index_name}'")
    
    return delta


def harvest_filter_HT1_alone(state_geom,
                              index_name='NBR',
                              mag_threshold=150):
    """
    HT1 — Hansen spectral thinning, no Lesiv filter.
    
    delta(index) > threshold  AND  NOT lossyear>0  AND  forest_union
    
    Returns BINARY mask at 30m native resolution.
    """
    delta = _compute_hansen_delta(index_name)
    hansen_any_loss = lossyear.gt(0)
    
    mask = (
        delta.gt(mag_threshold)
        .And(hansen_any_loss.unmask(0).Not())
        .updateMask(forest_union_mask)
        .selfMask()
        .clip(state_geom)
    )
    return mask


def harvest_filter_HT2_lesiv(state_geom,
                              index_name='NBR',
                              mag_threshold=150):
    """
    HT2 — Hansen spectral thinning × Lesiv managed forest.
    
    delta(index) > threshold  AND  NOT lossyear>0  
                             AND  forest_union  AND  lesiv_managed
    
    Stricter than HT1 — only detects thinning in managed forest.
    Returns BINARY mask at 30m native resolution.
    """
    delta = _compute_hansen_delta(index_name)
    hansen_any_loss = lossyear.gt(0)
    
    mask = (
        delta.gt(mag_threshold)
        .And(hansen_any_loss.unmask(0).Not())
        .And(lesiv_managed_30m)
        .updateMask(forest_union_mask)
        .selfMask()
        .clip(state_geom)
    )
    return mask


# ════════════════════════════════════════════════════════════════════════════════
# GROUP LT — LANDTRENDR (focus on LT3 pure thinning, NEGATION → BINARY)
# ════════════════════════════════════════════════════════════════════════════════

TM_BAND_NAMES = ['B1', 'B2', 'B3', 'B4', 'B5', 'B7']


def _mask_landsat_sr(image):
    qa = image.select('QA_PIXEL')
    cloud  = qa.bitwiseAnd(1 << 3).eq(0)
    shadow = qa.bitwiseAnd(1 << 4).eq(0)
    snow   = qa.bitwiseAnd(1 << 5).eq(0)
    return image.updateMask(cloud).updateMask(shadow).updateMask(snow)


def _prep_l5(image):
    scaled = (image.select(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B7'],
                           TM_BAND_NAMES)
              .multiply(0.0000275).add(-0.2)
              .multiply(10000).toUint16())
    return _mask_landsat_sr(image).addBands(scaled, overwrite=True).select(TM_BAND_NAMES)


def _prep_l89(image):
    scaled = (image.select(['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7'],
                           TM_BAND_NAMES)
              .multiply(0.0000275).add(-0.2)
              .multiply(10000).toUint16())
    return _mask_landsat_sr(image).addBands(scaled, overwrite=True).select(TM_BAND_NAMES)


def _build_annual_sr_composite(year, aoi):
    """Build annual 6-band TM-equivalent median composite. Hemisphere-aware."""
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
    images = [_build_annual_sr_composite(y, aoi)
              for y in range(start_year, end_year + 1)]
    return ee.ImageCollection.fromImages(images)


def _run_landtrendr(sr_collection, index_name='NBR'):
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
    change_image = lt.get_change_map({
        'delta':  'loss',
        'sort':   'greatest',
        'years':  {'start': start_year, 'end': end_year},
        'mag':    {'value': mag_threshold, 'operator': '>'},
        'mmu':    {'value': 11},
    })

    disturbance_mask = change_image.select('mag').gt(0).selfMask()
    year_image       = change_image.select('yod')
    return disturbance_mask, year_image


def harvest_filter_LT3_pure_thinning(region_geom, region_name,
                                      mag_threshold=200,
                                      start_year=2001,
                                      end_year=2022,
                                      index_name='NBR'):
    """LT3 — LandTrendr × Lesiv × NOT Hansen. Pure thinning, binary mask."""
    sr_collection = _build_sr_collection(region_geom, start_year, end_year)
    lt = _run_landtrendr(sr_collection, index_name)
    disturbance_mask, year_image = _get_change_mask(
        lt, start_year, end_year, mag_threshold
    )

    hansen_any_loss = lossyear.gt(0)

    mask = (disturbance_mask
            .And(lesiv_managed_30m)
            .And(hansen_any_loss.unmask(0).Not())
            .updateMask(forest_union_mask)
            .selfMask()
            .clip(region_geom))

    return mask, year_image
