#!/usr/bin/env python3

from json import dump
import os
from collections import defaultdict
from bs4 import BeautifulSoup
import requests
import pandas as pd

""" Data Table of Infant Length-for-age Charts """
_CDC_TABLES = {
    'length_cm_for_age_mos': "https://www.cdc.gov/growthcharts/html_charts/lenageinf.htm",
    'weight_kg_for_age_mos': "https://www.cdc.gov/growthcharts/html_charts/wtageinf.htm"
}

def extract_leading_numeral(string: str) -> int:
    for (index, character) in enumerate(string):
        if not character.isnumeric():
            break    
    else:
        index = len(string)
    return int(string[:index])
    
def get_sex_designation(string: str):
    if 'emale' in string:
        return 'F'
    if 'ale' in string:
        return 'M'
    raise ValueError(string) 

def main():
    result = defaultdict(defaultdict)
    for(name, url) in _CDC_TABLES.items():
        content = requests.get(url).content
        
        soup = BeautifulSoup(content, features='html.parser')
        for table in soup.find_all(lambda tag: tag.name=='table'):
            sex_designation = get_sex_designation(table.find(lambda tag: tag.name=='caption').text)

            data_frame_list = pd.read_html(str(table), index_col=0)

            if len(data_frame_list) != 1:
                raise ValueError('Could not retrieve table data')

            data_frame = data_frame_list[0]
            data_frame = data_frame.rename(extract_leading_numeral, axis='columns')

            result[name][sex_designation] = data_frame.to_dict()

    with open(os.path.join(os.path.dirname(__file__), 'cdc_data.json'), 'wt') as file_object:
        dump(result, file_object)

if __name__ == '__main__':
    main()