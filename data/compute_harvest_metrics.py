"""
═══════════════════════════════════════════════════════════════════════════════
 compute_metrics.py — BINARY MASK + SCALE PARAMETER VERSION
═══════════════════════════════════════════════════════════════════════════════

Computes area, volume, and residue metrics for BINARY masks (selfMask'd).
The actual computation scale is controlled by `selected_scale` parameter.

When you pass scale=1000, GEE projects all images to 1km internally and
computes per-1km-pixel values. Sims (1km native) stays unchanged. Hansen
and Lesiv get aggregated cleanly.

CRITICAL:
  - Mask values are 1 (selfMask'd, no zeros)
  - At scale=1000, each pixel = 100 ha
  - Total area = sum of pixelArea for masked pixels
  - Total volume = sum of (pixelArea_ha × volume_intensity_m³_ha)
  - Total residue = sum of (pixelArea_ha × residue_intensity_ODT_ha)

Conversions:
  VOLCFNET_L (ft³/acre) × 0.0699 = m³/ha
  DRYBIO_L (tons/acre) × 2.2417 = Mg/ha (= ODT/ha)
  Branch fraction: 0.275
═══════════════════════════════════════════════════════════════════════════════
"""

import ee


# Conversion constants
PIXEL_AREA_CONVERSION       = 1e4
VOL_FT3_PER_ACRE_TO_M3_HA   = 0.0699
BIO_TONS_PER_ACRE_TO_MG_HA  = 2.2417
BRANCH_FRACTION             = 0.275


def compute_metrics_export(mask,
                           region_geom,
                           region_name,
                           year,
                           filter_name,
                           selected_scale=1000,
                           treemap_vol=None,
                           treemap_bio=None,
                           annual_fraction=None,
                           extra_props=None,
                           export_folder='GEE_exports'):
    """
    Compute total area, volume, and residue from a binary mask
    at the specified scale and export as a single-row CSV.
    
    Parameters
    ----------
    mask : ee.Image
        Binary mask (selfMask'd) at native resolution.
    region_geom : ee.Geometry
        Region to reduce over.
    region_name : str
        Name of the region.
    year : int or str
        Year or year range.
    filter_name : str
        Name of the filter.
    selected_scale : int, default=1000
        Scale in meters for reduceRegion.
    treemap_vol : ee.Image or None
        TreeMap volume band (VOLCFNET_L) in ft³/acre.
    treemap_bio : ee.Image or None
        TreeMap biomass band (DRYBIO_L) in tons/acre.
    annual_fraction : ee.Image or None
        Annual fraction (1/rotation) for rotation-based tracks.
    extra_props : dict or None
        Additional metadata to add.
    export_folder : str
        Drive folder name.
    
    Returns
    -------
    ee.batch.Task
    """
    
    # Pixel area in hectares — depends on scale
    # At scale=1000: 1 km × 1 km = 100 ha per pixel
    pixel_area_ha = (
        ee.Image.pixelArea()
        .divide(PIXEL_AREA_CONVERSION)
        .updateMask(mask)
    )
    
    # If rotation-based, multiply by annual_fraction to annualize
    if annual_fraction is not None:
        effective_area = pixel_area_ha.multiply(annual_fraction)
    else:
        effective_area = pixel_area_ha
    
    # ── Build band stack ──
    bands = [effective_area.rename('area_ha')]

    if treemap_vol is not None:
        # Volume intensity in m³/ha
        vol_intensity = treemap_vol.multiply(VOL_FT3_PER_ACRE_TO_M3_HA)
        # Total volume per pixel = effective_area × intensity
        vol_m3 = effective_area.multiply(vol_intensity)
        bands.append(vol_m3.rename('vol_m3'))
        # Mean intensity for reporting
        bands.append(vol_intensity.updateMask(mask).rename('vol_m3_ha'))

    if treemap_bio is not None:
        # Residue intensity in ODT/ha
        residue_intensity = (
            treemap_bio
            .multiply(BIO_TONS_PER_ACRE_TO_MG_HA)
            .multiply(BRANCH_FRACTION)
        )
        # Total residue per pixel
        residue_ODT = effective_area.multiply(residue_intensity)
        bands.append(residue_ODT.rename('residue_ODT'))
        bands.append(residue_intensity.updateMask(mask).rename('residue_ODT_ha'))

    # ── Stack bands ──
    combined = bands[0]
    for b in bands[1:]:
        combined = combined.addBands(b)

    # ── Reduce: sum + mean in one pass ──
    stats = combined.reduceRegion(
        reducer=ee.Reducer.sum().combine(
            ee.Reducer.mean(),
            sharedInputs=True
        ),
        geometry=region_geom,
        scale=selected_scale,
        maxPixels=1e13,
        tileScale=16
    )

    # ── Build feature properties ──
    feature_props = {
        'region':      region_name,
        'year':        year,
        'filter_type': filter_name,
        'scale_m':     selected_scale,
        'area_ha':     stats.get('area_ha_sum'),
    }

    if treemap_vol is not None:
        feature_props['total_vol_m3']    = stats.get('vol_m3_sum')
        feature_props['mean_vol_m3_ha']  = stats.get('vol_m3_ha_mean')

    if treemap_bio is not None:
        feature_props['total_residue_ODT']   = stats.get('residue_ODT_sum')
        feature_props['mean_residue_ODT_ha'] = stats.get('residue_ODT_ha_mean')

    if extra_props:
        feature_props.update(extra_props)

    feature = ee.Feature(None, feature_props)
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
    print(f'🚀 {filter_name} | {region_name} | {year} | scale={selected_scale}m')

    return task
