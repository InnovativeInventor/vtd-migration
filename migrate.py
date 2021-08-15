import geopandas as gpd
import pandas as pd
import maup
import us
import os
import typer
from typing import List

import warnings; warnings.filterwarnings('ignore', 'GeoSeries.isna', UserWarning)

STATE_CRS_MAPPINGS = {"MA": "epsg:2249"}

def main(state_str: str, old_precinct_loc: str, epsilon_range = (7, 10), export_blocks: bool = False):
    state = us.states.lookup(state_str)
    crs = STATE_CRS_MAPPINGS[state_str]
    blocks = gpd.read_file(f"/home/max/git/census-process/final/{state_str.lower()}/{state_str.lower()}_block.shp").to_crs(crs)
    vtds = gpd.read_file(f"/home/max/git/census-process/final/{state_str.lower()}/{state_str.lower()}_vtd.shp").to_crs(crs)

    old_precincts = gpd.read_file(old_precinct_loc).to_crs(crs)
    election_cols = autodetect_election_cols(old_precincts.columns)

    # print(type(blocks["VAP"]))
    matches = close_matches(old_precincts, vtds)
    print("Number of matches:", len(matches), "unmatched:", len(vtds) - len(matches))
    matched_vtds = vtds.iloc[matches].copy()
    # unmatched_vtds = vtds.iloc[list(set(vtds.index) - set(matches))].copy()
    matched_precincts = old_precincts.iloc[matches.index].copy()
    unmatched_precincts = old_precincts.iloc[list(set(old_precincts.index) - set(matches.index))].copy()

    matched_precincts["matches"] = matches
    matched_vtds[election_cols] = matched_precincts.set_index("matches")[election_cols]
    print("Sum of absolute vote error on matched vtds", abs(matched_precincts[election_cols].sum() - matched_vtds[election_cols].sum()).sum())
    # matched_vtds[election_cols] = matches.map(matched_precincts[election_cols])
    # unmatched_vtds = transfer_votes(unmatched_precincts, unmatched_vtds, blocks, election_cols, scaling = "VAP", verbose = True)
    unmatched_vtds = transfer_votes(unmatched_precincts, vtds, blocks, election_cols, scaling = "VAP", verbose = True)# .iloc[list(set(vtds.index) - set(matches))].copy()

    combined_vtds = pd.concat([matched_vtds, unmatched_vtds])
    vtds[election_cols] = combined_vtds[election_cols].groupby(combined_vtds.index).agg("sum")
    print(vtds)
    print("(final) Sum of absolute vote error on vtds", abs(old_precincts[election_cols].sum() - vtds[election_cols].sum()).sum())
    vtds.to_file(f"products/{state_str.upper()}_vtd20.shp")

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
        if weights_vtd_diff < closest_weights_vtd_diff:
            weights = attempted_weights

    units[columns] = maup.prorate(assignment, source[columns], weights)

    assignment_to_target = maup.assign(units, target)
    target[columns] = units[columns].groupby(assignment_to_target).sum()

    if verbose:
        print("Sum of absolute vote error on blocks", abs(source[columns].sum() - units[columns].sum()).sum())
        print("Sum of absolute vote error on unmatched vtds", abs(source[columns].sum() - target[columns].sum()).sum())

    return target

def close_matches(source, target, threshold = 0.9):
    """
    Finds close matches in the source and target geometries (assumes that the threshold is > .5).
    """
    mapping = {}
    assignment = maup.assign(source, target)
    for count, source_geom in enumerate(source["geometry"]):
        target_geom = target.iloc[assignment.iloc[count]]["geometry"]
        # if (source_geom.intersection(target_geom).area / source_geom.union(target_geom).area) >= threshold:
        if (source_geom.intersection(target_geom).area / min(source_geom.area, target_geom.area)) >= threshold:
            mapping[count] = assignment.iloc[count]

    return pd.Series(mapping)

def autodetect_election_cols(columns):
    """
    Attempt to autodetect election cols from a given list
    """
    partial_cols = ["SEN", "PRES", "GOV", "TRE", "AG", "LTGOV", "AUD"]
    election_cols = [x for x in columns if any([x.startswith(y) for y in partial_cols])]
    if "SEND" in election_cols:
        del election_cols[election_cols.index("SEND")]
    return election_cols

if __name__ == "__main__":
    typer.run(main)
