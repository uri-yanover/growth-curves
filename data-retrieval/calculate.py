#!/usr/bin/env python3
from typing import List, Tuple, Dict
import os
import json
from collections import defaultdict
import click

def load_data():
    with open(os.path.join(os.path.dirname(__file__), 'cdc_data.json')) as file_obj:
        return json.load(file_obj)

@click.group()
@click.option('--sex', type=click.Choice(['M', 'F']))
@click.option('--age-mos', type=float)
@click.pass_context
def cli(ctx, sex, age_mos):
    ctx.obj = (sex, age_mos)

def adjust(y_desired, y_min, y_max, x_min, x_max):
    ratio = (y_desired - y_min) / (y_max - y_min)
    return x_min + ratio * (x_max - x_min)


def interpolate_key(data: Dict[float, float], search_value: float):
    sorted_inverted = sorted((value, key) for (key, value) in data.items())
    if search_value < sorted_inverted[0][0]:
        raise ValueError('Value too small')
    if search_value > sorted_inverted[-1][0]:
        raise ValueError('Value too large')
    if search_value == sorted_inverted[0][0]:
        return sorted_inverted[0][1]
    if search_value == sorted_inverted[-1][0]:
        return sorted_inverted[-1][1]

    prev_key = None
    prev_value = None
    for (value, key) in sorted_inverted:
        if search_value == value:
            return key
        if search_value < value:
            # we found!
            break     
        prev_key = key
        prev_value = value

    return adjust(search_value,
                  prev_value,
                  value,
                  prev_key,
                  key)

def find_relevant_data_points_for_age( 
    data: Dict[int, Dict[float, float]],
    weight: float,
    age_mos: float) -> List[Tuple[float, float]]:
    sorted_keys = sorted(data.keys())
    if age_mos < sorted_keys[0]:
        raise ValueError('Out of range - age too small')
    if age_mos > sorted_keys[-1]:
        raise ValueError('Out of range - age too large')
    if age_mos == sorted_keys[0]:
        return interpolate_key(data, data[sorted_keys[0]])
    if age_mos == sorted_keys[-1]:
        return interpolate_key(data, data[sorted_keys[-1]])

    for (index, value) in enumerate(sorted_keys):
        if value > age_mos:
            break
    # we know that the value is between index and idex + 1
    left_percentile = interpolate_key(data[sorted_keys[index-1]], weight)
    right_percentile = interpolate_key(data[sorted_keys[index]], weight)

    return adjust(age_mos,
                  sorted_keys[index-1],
                  sorted_keys[index],
                  left_percentile, 
                  right_percentile)

def reorder(idx0, idx1, idx2, data):
    result = defaultdict(defaultdict)

    for (v0, d0) in data.items():
        for (v1, v2) in d0.items():
            flat = (float(v0), float(v1), float(v2))
            result[flat[idx0]][flat[idx1]] = flat[idx2]
    return result

@click.command()
@click.option('--weight', type=float, required=True)
@click.pass_obj
def weight_percentile(obj, weight):
    (sex, age_mos) = obj
    # data layout is: percentile -> age (mos) -> weight
    # We will alter it into age(mos) -> percentile -> weight
    data = reorder(1, 0, 2, load_data()['weight_kg_for_age_mos'][sex])
    print(find_relevant_data_points_for_age(data, weight, age_mos))
    

cli.add_command(weight_percentile)

if __name__ == '__main__':
    cli()
    