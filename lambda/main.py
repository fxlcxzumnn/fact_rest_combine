import datetime
import pickle
import tempfile
import boto3
import os.path
import pytz
import google_sheet
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from urllib.parse import urlparse
import itertools
import string
import difflib

#TOKEN_PICKLE_PATH='token.pickle'

def num_only(x):
    x = filter(lambda i:i in string.digits,x)
    x = list(x)
    x = ''.join(x)
    return x

def get_phone_no_list(phoneNo):
    phone_no_list = [phoneNo]
    phone_no_list = itertools.chain.from_iterable(map(lambda i:i.split('/'),phone_no_list))
    phone_no_list = itertools.chain.from_iterable(map(lambda i:i.split(','),phone_no_list))
    phone_no_list = map(num_only,phone_no_list)
    phone_no_list = filter(lambda i:i, phone_no_list)
    phone_no_list = list(phone_no_list)
    return phone_no_list

def main(spreadsheet_id, sheet_title, token_pickle_url):
    print('PGTXOXUVLI')

    start_datetime_str = str(datetime.datetime.now(tz=pytz.timezone('Hongkong')))

    with tempfile.TemporaryDirectory() as tmpdir:
        parse_result = urlparse(token_pickle_url)
        s3_bucket = parse_result.netloc
        s3_path = parse_result.path.lstrip('/')

        token_pickle_fn = os.path.join(tmpdir,'token.pickle')
        #session = boto3.Session(profile_name='fxl')
        session = boto3.Session()
        s3 = session.client('s3')
        s3.download_file(s3_bucket, s3_path, token_pickle_fn)

        with open(token_pickle_fn, 'rb') as token:
            creds = pickle.load(token)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_pickle_fn, 'wb') as token:
                pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    spreadsheets_service = service.spreadsheets()

    config = google_sheet.get_value_list_list(spreadsheet_id, sheet_title, spreadsheets_service)
    config = google_sheet.value_list_list_to_dict(config)
    #print(config)
    
    print('PJZLNSBOAT')
    
    restautant_data_list = google_sheet.get_value_list_list(
        spreadsheet_id = config['input_be_spreadsheet_id'],
        sheet_title = config['input_be_sheet_title'],
        spreadsheets = spreadsheets_service,
    )

    print('LPILIMTNSS')

    restautant_data_list,_ = google_sheet.value_list_list_to_value_dict_list(restautant_data_list)
    restautant_data_list = map(
        lambda i: {
            'rest_is_active':       i[config['input_be_is_active_col_name']],
            'rest_id':              i[config['input_be_id_col_name']],
            'rest_name':            i[config['input_be_name_col_name']],
            'rest_phone_str':       i[config['input_be_phone_no_col_name']],
            'rest_phone_no_list':   get_phone_no_list(i[config['input_be_phone_no_col_name']]),
            'rest_address':         i[config['input_be_address_col_name']],
        },
       restautant_data_list
    )
    restautant_data_list = filter(
        lambda i: i['rest_is_active']=='TRUE',
        restautant_data_list
    )
    restautant_data_list = filter(
        lambda i: i['rest_id'],
        restautant_data_list
    )
    restautant_data_list = list(restautant_data_list)
    #print(restautant_data_list)
    
    name_to_rest_id_list_dict = {}
    phone_no_to_rest_id_list_dict = {}
    rest_id_to_rest_data_dict = {}
    for restautant_data in restautant_data_list:
        name_to_rest_id_list_dict[restautant_data['rest_name']] = []
        for phone_no in restautant_data['rest_phone_no_list']:
            phone_no_to_rest_id_list_dict[phone_no] = []

    for restautant_data in restautant_data_list:
        rest_id_to_rest_data_dict[restautant_data['rest_id']] = restautant_data
        name_to_rest_id_list_dict[restautant_data['rest_name']].append(restautant_data['rest_id'])
        for phone_no in restautant_data['rest_phone_no_list']:
            phone_no_to_rest_id_list_dict[phone_no].append(restautant_data['rest_id'])

    print('QJKAXNARCK')

    fact_data_list = google_sheet.get_value_list_list(
        spreadsheet_id = config['input_fact_spreadsheet_id'],
        sheet_title = config['input_fact_sheet_title'],
        spreadsheets = spreadsheets_service,
    )

    print('EJKQPZSGYJ')

    fact_data_list,_ = google_sheet.value_list_list_to_value_dict_list(fact_data_list)
    for idx in range(len(fact_data_list)):
        fact_data_list[idx]['fact_row'] = idx+2
    fact_data_list = map(
        lambda i: {
            'fact_row':             i['fact_row'],
            'fact_timestamp':       i[config['input_fact_timestamp_col_name']],
            'fact_name':            i[config['input_fact_name_col_name']],
            'fact_address':         i[config['input_fact_address_col_name']],
            'fact_phone_str':       i[config['input_fact_phone_col_name']],
            'fact_phone_no_list':   get_phone_no_list(i[config['input_fact_phone_col_name']]),
            'rest_id':              '',
        },
       fact_data_list
    )
    fact_data_list = list(fact_data_list)
    #print(fact_data_list)

    for fact_data in fact_data_list:
        if fact_data['rest_id']: continue
        rest_id_set = set()
        for fact_phone_no in fact_data['fact_phone_no_list']:
            if fact_phone_no not in phone_no_to_rest_id_list_dict: continue
            for rest_id in phone_no_to_rest_id_list_dict[fact_phone_no]:
                rest_id_set.add(rest_id)
        rest_id_list = list(rest_id_set)
        if len(rest_id_list) == 0: continue
        if len(rest_id_list) == 1:
            fact_data['rest_id'] = rest_id_list[0]
            continue
        fact_address = fact_data['fact_address']
        address_to_rest_id_dict = {
            rest_id_to_rest_data_dict[rest_id]['rest_address']: rest_id
            for rest_id in rest_id_list
        }
        best_address_list = difflib.get_close_matches(fact_address, address_to_rest_id_dict, n=1)
        if not best_address_list: continue
        rest_id = address_to_rest_id_dict[best_address_list[0]]
        fact_data['rest_id'] = rest_id

    for fact_data in fact_data_list:
        if fact_data['rest_id']: continue
        fact_name = fact_data['fact_name']
        if fact_name not in name_to_rest_id_list_dict: continue
        rest_id_list = name_to_rest_id_list_dict[fact_name]
        if len(rest_id_list) == 1:
            fact_data['rest_id'] = rest_id_list[0]
            continue
        fact_address = fact_data['fact_address']
        address_to_rest_id_dict = {
            rest_id_to_rest_data_dict[rest_id]['rest_address']: rest_id
            for rest_id in rest_id_list
        }
        best_address_list = difflib.get_close_matches(fact_address, address_to_rest_id_dict, n=1)
        if not best_address_list: continue
        rest_id = address_to_rest_id_dict[best_address_list[0]]
        fact_data['rest_id'] = rest_id

    for fact_data in fact_data_list:
        if not fact_data['rest_id']: continue
        rest_id = fact_data['rest_id']
        rest_data = rest_id_to_rest_data_dict[rest_id]
        fact_data['rest_name'] = rest_data['rest_name']
        fact_data['rest_phone_str'] = rest_data['rest_phone_str']
        fact_data['rest_address'] = rest_data['rest_address']

    print('CILUWIONXV')

    sheet_title_list = google_sheet.get_sheet_title_list(
        config['output_spreadsheet_id'],
        spreadsheets_service
    )
    if config['output_sheet_title'] not in sheet_title_list:
        google_sheet.add_sheet(config['output_spreadsheet_id'], config['output_sheet_title'], spreadsheets_service)

    output_col_list = [
        'fact_row',
        'fact_timestamp',
        'rest_id',
        'fact_name', 'rest_name',
        'fact_phone_str', 'rest_phone_str',
        'fact_address', 'rest_address',
    ]
    output_value_list_list = google_sheet.value_dict_list_to_value_list_list(
        fact_data_list, output_col_list
    )
    google_sheet.set_value_list_list(
        spreadsheet_id  = config['output_spreadsheet_id'],
        sheet_title     = config['output_sheet_title'],
        value_list_list = output_value_list_list,
        spreadsheets    = spreadsheets_service,
    )

    sheet_title_list = google_sheet.get_sheet_title_list(
        config['var_spreadsheet_id'],
        spreadsheets_service
    )
    if config['var_sheet_title'] not in sheet_title_list:
        google_sheet.add_sheet(config['var_spreadsheet_id'], config['var_sheet_title'], spreadsheets_service)
    
    var_dict = {
        'update_date': start_datetime_str
    }
    var_value_list_list = google_sheet.dict_to_value_list_list(var_dict)
    google_sheet.set_value_list_list(
        spreadsheet_id  = config['var_spreadsheet_id'],
        sheet_title     = config['var_sheet_title'],
        value_list_list = var_value_list_list,
        spreadsheets    = spreadsheets_service,
    )

    print('TYHDJWYKMC')

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Google sheet to csv/json')
    parser.add_argument('spreadsheet_id', type=str)
    parser.add_argument('sheet_title', type=str)
    parser.add_argument('token_pickle_url', type=str)
    args = parser.parse_args()

    main(
        spreadsheet_id      = args.spreadsheet_id,
        sheet_title         = args.sheet_title,
        token_pickle_url    = args.token_pickle_url,
    )
