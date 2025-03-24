__author__ = "PyPSA meets Earth"
__copyright__ = "Copyright 2022, The PyPSA meets Earth Initiative"
__license__ = "MIT"

"""Filter the Extracted OSM Data

This module filters the extracted OSM data.

"""
import time
import json
import logging
import os
from datetime import datetime

from earth_osm.tagdata import get_feature_list
from earth_osm.extract import filter_pbf
from earth_osm.gfk_download import download_pbf
from earth_osm.osmpbf import Node, Relation, Way
from earth_osm import logger as base_logger

logger=logging.getLogger("eo.filter")
logger.setLevel(logging.INFO)


def feature_filter(primary_data, filter_tuple = ('power', 'line')):

    if set(primary_data.keys()) != set(['Node', 'Way', 'Relation']):
        logger.error('malformed primary_data')

    feature_data = {'Node': {}, 'Way': {}, 'Relation': {}}
    for element in list(feature_data.keys()):
        for id in primary_data[element]:
            if filter_tuple in primary_data[element][id]["tags"].items():
                feature_data[element][id] = primary_data[element][id]
    return feature_data


def run_feature_filter(primary_dict, feature_name):
    logger.info("4.5 Running feature filter.....")
    if feature_name[:4] == 'ALL_':
        logger.info('Using ALL wildcard, so feature filter is skipped')
        return primary_dict
    
    primary_name = primary_dict['Metadata']['primary_feature']
    filter_tuple = (primary_name, feature_name)
    primary_data = primary_dict['Data']

    feature_data = feature_filter(primary_data, filter_tuple)

    metadata = {
        'filter_date': str(datetime.now().isoformat()),
        'filter_tuple': json.dumps(filter_tuple),
    }

    feature_dict = {
        'Metadata': metadata,
        'Data':feature_data
        }

    return feature_dict


def run_primary_filter(PBF_inputfile, primary_file, primary_name, feature_name, multiprocess):
    logger.info('6.0 Running primary filter... New Pre-Filter Data')
    feature_list = get_feature_list(primary_name)
    logger.info(f"6.1 Got feature list!: {primary_name, feature_list}")
    pre_filter = {
        Node: {primary_name: feature_list},
        Way: {primary_name: feature_list},
        Relation: {primary_name: feature_list},
    }
    logger.info("6.2 Running filter_pbf...")
    primary_data = filter_pbf(PBF_inputfile, pre_filter, multiprocess)
    logger.info("6.3 Ran filter_pbf successfully!")
    metadata = {
        'filter_date': str(datetime.now().isoformat()),
        'primary_feature': primary_name,
    }
    primary_dict = {
        'Metadata': metadata,
        'Data': primary_data
    }
    # Save primary_dict
    logger.info("6.4 Saving primary_dict....")
    with open(primary_file, "w", encoding="utf-8") as target:
        json.dump(
            primary_dict,
            target,
            ensure_ascii=False,
            indent=4,
            separators=(",", ":"),
        )

    return primary_dict


def get_filtered_data(region, primary_name, feature_name, mp, update, data_dir, progress_bar=True):
    
    logger.info(f"""4.0 Getting filtered data: 
                \nRegion: {region},
                \nprimary_name: {primary_name}, 
                \nfeature_name: {feature_name},
                \nmultiprocessing: {mp}, 
                \nupdate: {update}, 
                \ndata_dir: {data_dir}
                """)
    geofabrik_pbf_url = region.urls['pbf']
    logger.info(f"4.01 Downloading PBF files... {geofabrik_pbf_url, update, data_dir, progress_bar}")
    PBF_inputfile = download_pbf(geofabrik_pbf_url, update, data_dir, progress_bar=progress_bar)
    logger.info("4.05 PBD File Downloaded")
    country_code = region.short
    logger.info("4.1 PBF exists. Checking primary file")
    # ------- primary file -------
    primary_file_exists = False
    primary_file = os.path.join(data_dir, primary_name, f"{country_code}_{primary_name}.json"
    )

    if os.path.exists(primary_file):
        logger.info("4.1 Load existing primary file")
        primary_file_exists = True
        with open(primary_file, encoding="utf-8") as f:
            primary_dict = json.load(f)
    else:
        logger.info("4.2 Create primary file")
        os.makedirs(os.path.dirname(primary_file), exist_ok=True)

    # TODO: compare update time using metadata in primary_dict
    if not primary_file_exists or update is True:
        logger.info(f"4.25 Primary file exist: {primary_file_exists}, Update: {update}. Running primary filter...")
        primary_dict = run_primary_filter(PBF_inputfile, primary_file, primary_name, feature_name, mp)
    else:
        logger.info("4.3 Primary file exists and update is False")
    # ------- feature file -------
    logger.info(f"4.4 Running feature filter: {len(primary_dict['Data']['Node'])} Nodes, {len(primary_dict['Data']['Way'])} Ways, {len(primary_dict['Data']['Relation'])} Relations")
    feature_dict = run_feature_filter(primary_dict, feature_name)
    return primary_dict, feature_dict


