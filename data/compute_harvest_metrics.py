"""
═══════════════════════════════════════════════════════════════════════════════
 compute_metrics.py — FINAL DUAL-METHOD VERSION
═══════════════════════════════════════════════════════════════════════════════

Handles BOTH mask types:
  - mask_type='fractional': for A1, A2 (positive identity, fractional 1km)
                            mask values are 0.0–1.0 (fraction of cell satisfying)
                            Total = sum(fraction × pixelArea × intensity)
  
  - mask_type='binary': for A4, A5, A6, LT3 (selfMask'd binary)
                        mask values are 1 (or null)
                        Total = sum(pixelArea × intensity) for masked pixels

Both produce CORRECT total values at scale=1000.

Conversions:
  VOLCFNET_L (ft³/acre) × 0.0699  = m³/ha
  DRYBIO_L (tons/acre) × 2.2417   = Mg/ha (= ODT/ha)
  Branch fraction: 0.275
═══════════════════════════════════════════════════════════════════════════════
"""

import ee


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
                           mask_type='binary',
                           treemap_vol=None,
                           treemap_bio=None,
                           annual_fraction=None,
                           extra_props=None,
                           export_folder='GEE_exports'):
    """
    Compute total area, volume, and residue and export as a single-row CSV.
    
    Parameters
    ----------
    mask : ee.Image
        Either a fractional 0-1 mask (mask_type='fractional')
        or a binary selfMask'd mask (mask_type='binary').
    mask_type : {'fractional', 'binary'}
        - 'fractional': A1, A2 (use ×fraction in computation)
        - 'binary':     A4, A5, A6, LT3, B1a (selfMask handles it)
    annual_fraction : ee.Image or None
        For rotation-based tracks (A4, A5, A6).
    selected_scale : int, default=1000
        Computation scale in meters.
    """
    
    if mask_type not in ('fractional', 'binary'):
        raise ValueError(f"mask_type must be 'fractional' or 'binary', got '{mask_type}'")
    
    pixel_area_ha_full = ee.Image.pixelArea().divide(PIXEL_AREA_CONVERSION)
    
    # ── Build effective_area (the "weight" per cell) ──
    if mask_type == 'fractional':
        # Fractional: each cell holds fraction 0-1 of harvested area
        # effective_area = fraction × pixel_area
        effective_area = mask.multiply(pixel_area_ha_full)
        # For mean intensity: use mask>0 to define the support
        intensity_mask = mask.gt(0)
    else:
        # Binary: selfMask'd, mask values are 1 where present
        # effective_area = pixel_area, masked
        effective_area = pixel_area_ha_full.updateMask(mask)
        intensity_mask = mask
    
    # Apply rotation cycle if provided (rotation tracks: A3, A4, A5, A6)
    if annual_fraction is not None:
        effective_area = effective_area.multiply(annual_fraction)
    
    # ── Build band stack ──
    bands = [effective_area.rename('area_ha')]

    if treemap_vol is not None:
        vol_intensity = treemap_vol.multiply(VOL_FT3_PER_ACRE_TO_M3_HA)  # m³/ha
        vol_m3 = effective_area.multiply(vol_intensity)
        bands.append(vol_m3.rename('vol_m3'))
        bands.append(vol_intensity.updateMask(intensity_mask).rename('vol_m3_ha'))

    if treemap_bio is not None:
        residue_intensity = (
            treemap_bio
            .multiply(BIO_TONS_PER_ACRE_TO_MG_HA)
            .multiply(BRANCH_FRACTION)
        )
        residue_ODT = effective_area.multiply(residue_intensity)
        bands.append(residue_ODT.rename('residue_ODT'))
        bands.append(residue_intensity.updateMask(intensity_mask).rename('residue_ODT_ha'))

    # ── Stack bands ──
    combined = bands[0]
    for b in bands[1:]:
        combined = combined.addBands(b)

    # ── Reduce: sum + mean ──
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
        'mask_type':   mask_type,
        'area_ha':     stats.get('area_ha_sum'),
    }

    if treemap_vol is not None:
        feature_props['total_vol_m3']   = stats.get('vol_m3_sum')
        feature_props['mean_vol_m3_ha'] = stats.get('vol_m3_ha_mean')

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
    print(f'🚀 {filter_name} | {region_name} | {year} | scale={selected_scale}m | type={mask_type}')

    return task
