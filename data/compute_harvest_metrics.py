"""
═══════════════════════════════════════════════════════════════════════════════
 compute_metrics.py — 1km FRACTIONAL MASK VERSION
═══════════════════════════════════════════════════════════════════════════════

Computes area, volume, and residue metrics for FRACTIONAL masks at 1km resolution.

Key change from previous version:
  - Mask values are now fractions (0.0 to 1.0), not binary
  - Total area = fraction × pixel_area_ha (per cell), summed across region
  - Total volume = fraction × pixel_area_ha × volume_intensity (m³/ha)
  - Total residue = fraction × pixel_area_ha × residue_intensity (ODT/ha)
  
This gives MATHEMATICALLY CORRECT totals at any scale.

Conversions:
  VOLCFNET_L (ft³/acre) × 0.0699 = m³/ha
  DRYBIO_L (tons/acre) × 2.2417 = Mg/ha (= ODT/ha)
  Branch fraction: 0.275 (typical residue from total above-ground biomass)
═══════════════════════════════════════════════════════════════════════════════
"""

import ee


# Conversion constants
PIXEL_AREA_CONVERSION       = 1e4      # m² to ha
VOL_FT3_PER_ACRE_TO_M3_HA   = 0.0699   # TreeMap volume conversion
BIO_TONS_PER_ACRE_TO_MG_HA  = 2.2417   # TreeMap biomass conversion
BRANCH_FRACTION             = 0.275    # Branch residue fraction


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
    Compute total area, volume, and residue from a FRACTIONAL mask
    and export as a single-row CSV.
    
    Parameters
    ----------
    mask : ee.Image
        Fractional mask at scale=selected_scale (values 0.0 to 1.0).
    region_geom : ee.Geometry
        Region to reduce over.
    region_name : str
        Name of the region (for filename and CSV column).
    year : int or str
        Year or year range (e.g. 'all_2001_2022').
    filter_name : str
        Name of the filter (e.g. 'A2_H_S_L', 'LT3_pure_thinning_NBR_mag200').
    selected_scale : int, default=1000
        Scale in meters for reduceRegion.
    treemap_vol : ee.Image or None
        TreeMap volume band (VOLCFNET_L) in ft³/acre. If None, no volume calc.
    treemap_bio : ee.Image or None
        TreeMap biomass band (DRYBIO_L) in tons/acre. If None, no residue calc.
    annual_fraction : ee.Image or None
        Annual fraction image (1/rotation_yrs) for rotation-based tracks.
        Multiplies into both area and volume/residue to give annualized totals.
    extra_props : dict or None
        Additional metadata to add to the output feature.
    export_folder : str
        Drive folder name for the CSV.
    
    Returns
    -------
    ee.batch.Task
        Started export task.
    """
    
    # Pixel area in hectares (depends on scale)
    # At 1km scale: each pixel = 1,000,000 m² = 100 ha
    pixel_area_ha = ee.Image.pixelArea().divide(PIXEL_AREA_CONVERSION)
    
    # Effective area per cell = fraction × pixel_area_ha
    # If annual_fraction provided, also multiply by 1/rotation
    if annual_fraction is not None:
        effective_area_per_cell = mask.multiply(pixel_area_ha).multiply(annual_fraction)
    else:
        effective_area_per_cell = mask.multiply(pixel_area_ha)
    
    # ── Build band stack ──
    bands = [effective_area_per_cell.rename('area_ha')]

    if treemap_vol is not None:
        # Volume in m³ per cell = effective_area × volume_intensity
        vol_intensity = treemap_vol.multiply(VOL_FT3_PER_ACRE_TO_M3_HA)  # m³/ha
        vol_m3_per_cell = effective_area_per_cell.multiply(vol_intensity)
        bands.append(vol_m3_per_cell.rename('vol_m3'))
        
        # Also save intensity separately for mean calc
        bands.append(vol_intensity.updateMask(mask).rename('vol_m3_ha'))

    if treemap_bio is not None:
        # Residue intensity: biomass × branch fraction = ODT/ha
        residue_intensity = (
            treemap_bio
            .multiply(BIO_TONS_PER_ACRE_TO_MG_HA)
            .multiply(BRANCH_FRACTION)
        )
        residue_ODT_per_cell = effective_area_per_cell.multiply(residue_intensity)
        bands.append(residue_ODT_per_cell.rename('residue_ODT'))
        
        bands.append(residue_intensity.updateMask(mask).rename('residue_ODT_ha'))

    # ── Stack bands ──
    combined = bands[0]
    for b in bands[1:]:
        combined = combined.addBands(b)

    # ── Reduce — sum + mean in one pass ──
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
        feature_props['total_residue_ODT']    = stats.get('residue_ODT_sum')
        feature_props['mean_residue_ODT_ha']  = stats.get('residue_ODT_ha_mean')

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
