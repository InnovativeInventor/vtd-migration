import geopandas as gpd
import pandas as pd
import maup
import us
import os
import typer
from typing import List
from shapely import wkt
import repair_gdf_jc_v1_2
import tqdm

import warnings; warnings.filterwarnings('ignore', 'GeoSeries.isna', UserWarning)
# maup.progress.enabled = True

STATE_CRS_MAPPINGS = {
    "MA": "epsg:2249",
    "MI": "epsg:6493",
    "AK": "epsg:3338",
    "UT": "epsg:26912",
    "IN": "epsg:2965",
    "VA": "epsg:3968",
    "AZ": "epsg:2223",
    "NM": "epsg:32613",
    "TX": "epsg:3081",
    "PA": "epsg:26918",
    "OH": "epsg:3747",
    "WI": "epsg:26916",
    "OR": "epsg:2338",
    "MO": "epsg:32615",
    "MD": "epsg:26985",
    "NC": "epsg:6543",
    "NH": "epsg:3437",
    "PR": "epsg:3920",
    "NE": "epsg:6516",
    "ME": "epsg:6348",
    "WA": "epsg:6339",
    "LA": "epsg:6476",
    "MN": "epsg:26915",
    "DE": "epsg:2235",
    "CT": "epsg:26956",
    "GA": "epsg:32617", # used to be epsg:4019, a geographic CRS
    "CO": "epsg:2957",
    "OK": "epsg:2957",
    "RI": "epsg:3438"
}

def main(state_str: str, old_precinct_loc: str, vtd_loc = None, output_loc = None, epsilon_range = (7, 10), export_blocks: bool = False, repair: bool = False):
    state = us.states.lookup(state_str)
    crs = STATE_CRS_MAPPINGS[state_str]
    blocks = gpd.read_file(f"/home/max/git/census-process/final/{state_str.lower()}/{state_str.lower()}_block.shp").to_crs(crs)
    counties = gpd.read_file(f"/home/max/git/census-process/final/{state_str.lower()}/{state_str.lower()}_county.shp").to_crs(crs)

    if not vtd_loc:
        vtd_loc = f"/home/max/git/census-process/final/{state_str.lower()}/{state_str.lower()}_vtd.shp"
    vtds = gpd.read_file(vtd_loc).to_crs(crs)

    old_precincts = gpd.read_file(old_precinct_loc).to_crs(crs)
    # old_precincts["geometry"] = old_precincts["geometry"].apply(lambda x: wkt.loads(str(x)))
    old_precincts["geometry"] = old_precincts["geometry"].buffer(0)# .simplify()
    if repair:
        old_precincts = repair_gdf_jc_v1_2.repair_gdf_jc(old_precincts, close_gaps=False).reset_index()

    election_cols = autodetect_election_cols(old_precincts.columns)

    # matches = close_matches(old_precincts, vtds)
    combined_counties_vtds = []
    # county_matched_vtds = close_matches(vtds, counties)
    county_matched_vtds = maup.assign(vtds, counties)
    # county_matched_precincts = close_matches(old_precincts, counties)
    county_matched_precincts = maup.assign(old_precincts, counties)
    for county in set(county_matched_vtds.values):
        county_vtds = vtds.iloc[[k for k, v in county_matched_vtds.items() if v==county]]
        county_precincts = old_precincts.iloc[[k for k, v in county_matched_precincts.items() if v==county]]

        matches = close_matches(county_vtds, county_precincts, reverse=True)
        matched_vtds = county_vtds.loc[matches].copy()
        # unmatched_vtds = vtds.iloc[list(set(vtds.index) - set(matches))].copy()
        matched_precincts = county_precincts.loc[matches.index].copy()
        unmatched_precincts = county_precincts.loc[list(set(county_precincts.index) - set(matches.index))].copy()
        print("County:", county, "Number of matches:", len(matches), "unmatched:", len(unmatched_precincts))

        matched_precincts["matches"] = matches
        matched_vtds[election_cols] = matched_precincts.set_index("matches")[election_cols]
        print("Sum of absolute vote error on matched vtds", abs(matched_precincts[election_cols].sum() - matched_vtds[election_cols].sum()).sum())
        # matched_vtds[election_cols] = matches.map(matched_precincts[election_cols])
        # unmatched_vtds = transfer_votes(unmatched_precincts, unmatched_vtds, blocks, election_cols, scaling = "VAP", verbose = True)
        if len(unmatched_precincts):
            unmatched_vtds = transfer_votes(unmatched_precincts, vtds, blocks, election_cols, scaling = "VAP", verbose = True)# .iloc[list(set(vtds.index) - set(matches))].copy()
            combined_counties_vtds.append(pd.concat([matched_vtds, unmatched_vtds]))
        else:
            combined_counties_vtds.append(matched_vtds)

    combined_vtds = pd.concat(combined_counties_vtds)

    vtds[election_cols] = combined_vtds[election_cols].groupby(combined_vtds.index).agg("sum")

    print(vtds)
    print(f"(final) Sum of absolute vote error on all vtds on {state_str}", abs(old_precincts[election_cols].sum() - vtds[election_cols].sum()).sum())
    assert abs(old_precincts[election_cols].sum() - vtds[election_cols].sum()).sum() < 1, f"{state_str}"
    if not output_loc:
        vtds.to_file(f"products/{state_str.upper()}_vtd20.shp")
    else:
        vtds.to_file(output_loc)

    if export_blocks:
        blocks.to_file(f"products/{state_str.upper()}_block20.shp")

def transfer_votes(source: gpd.GeoDataFrame, target: gpd.GeoDataFrame, units: gpd.GeoDataFrame, columns: List[str], epsilon_range = (7, 10), scaling = "VAP", verbose = False):
    assignment = maup.assign(units, source)

    closest_weights_vtd_diff = len(target)
    start, stop = epsilon_range
    for epsilon_magnitude in range(start, stop+1):
        epsilon = pow(10, -1 * epsilon_magnitude)

        units_adjusted = units[scaling].replace(0, epsilon)

        if verbose:
            print("Sums diff:", units_adjusted.sum() - units_adjusted.sum(), "with epsilon:", epsilon)

        attempted_weights = units_adjusted / assignment.map(units_adjusted.groupby(assignment).sum())
        weights_vtd_diff = attempted_weights.sum() - len(target)
        if weights_vtd_diff <= closest_weights_vtd_diff:
            weights = attempted_weights

    units[columns] = maup.prorate(assignment, source[columns], weights)

    assignment_to_target = maup.assign(units, target)
    target[columns] = units[columns].groupby(assignment_to_target).sum()

    if verbose:
        print("Sum of absolute vote error on blocks", abs(source[columns].sum() - units[columns].sum()).sum())
        print("Sum of absolute vote error on unmatched vtds", abs(source[columns].sum() - target[columns].sum()).sum())

    return target

def close_matches(source, target, threshold = 0.9, reverse = False):
    """
    Finds close matches in the source and target geometries (assumes that the threshold is > .5).
    """
    mapping = {}
    assignment = maup.assign(source, target)
    for count, source_geom in source["geometry"].items():
        try:
            target_geom = target["geometry"][assignment[count]]
        except KeyError:
            continue

        # if (source_geom.intersection(target_geom).area / source_geom.union(target_geom).area) >= threshold:
        if (source_geom.intersection(target_geom).area / min(source_geom.area, target_geom.area)) >= threshold:
            if reverse:
                mapping[assignment[count]] = count
            else:
                mapping[count] = assignment[count]

    return pd.Series(mapping)

def autodetect_election_cols(columns):
    """
    Attempt to autodetect election cols from a given list
    """
    partial_cols = ["SEN", "PRES", "GOV", "TRE", "AG", "LTGOV", "AUD", "USH", "SOS", "CAF"]
    election_cols = [x for x in columns if any([x.startswith(y) for y in partial_cols])]

    if "SEND" in election_cols:
        del election_cols[election_cols.index("SEND")]
    if "SENDIST" in election_cols:
        del election_cols[election_cols.index("SENDIST")]

    return election_cols

if __name__ == "__main__":
    typer.run(main)
