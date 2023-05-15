# -*- coding: utf-8 -*-
"""
Created on Mon May 15 00:03:38 2023

@author: marcl
"""

import requests

BIN_API_URL = r'https://api.jsonbin.io/v3/b'

def load_data_jsonbin(api_key, bin_id):
    url = BIN_API_URL + '/' + bin_id + '/latest'
    headers = {'X-Master-Key': api_key}
    res = requests.get(url, headers=headers).json()
    return res['record']

def save_data_jsonbin(api_key, bin_id, data):
    url = BIN_API_URL + '/' + bin_id
    headers = {'X-Master-Key': api_key, 'Content-Type': 'application/json'}
    res = requests.put(url, headers=headers, json=data).json()
    return res
