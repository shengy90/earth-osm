import pandas as pd
import logging

from earth_osm.taginfo import get_tag_data
from earth_osm import logger as base_logger

logger = logging.getLogger("eo.tag")
logger.setLevel(logging.INFO)


tag_data = get_tag_data()

def get_feature_list(primary_name):
    logger.info(f"8.0 Getting feature list...")
    feature_list = list(tag_data[primary_name]['features'].keys())
    logger.info(f"8.1 Got feature list: {len(feature_list)}")
    return feature_list

def get_primary_list():
    return list(tag_data.keys())

def load_tag_data():
    # load tag_data into a dataframe
    dataframes = []
    json_dict = tag_data
    for primary_key, values in json_dict.items():
        features = values['features']
        for feature_key, feature_values in features.items():
            df = pd.json_normalize(feature_values)
            dataframes.append(df)

    tag_df = pd.concat(dataframes, ignore_index=True)
    return tag_df

#%%
def get_popular_features(primary_name):
    # TODO: check count_all and only return
    # - features that are significant
    # - features that are non-relation
    return get_feature_list(primary_name)
    
