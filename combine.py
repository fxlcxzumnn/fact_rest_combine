import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
import argparse
import itertools
import string
import difflib

def get_data(row, idx):
    if len(row) <= idx: return ''
    return row[idx]

def read_json(fn):
    with open(fn,'r') as fin:
        return json.load(fin)

def write_json(fn,data):
    with open(fn,'w') as fout:
        json.dump(data,fout,sort_keys=True,indent=2,ensure_ascii=False)
        fout.write('\n')

def num_only(x):
    x = filter(lambda i:i in string.digits,x)
    x = list(x)
    x = ''.join(x)
    return x

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Combine fact and restaurant data')
    parser.add_argument('config_file', type=str, help='config file')
    args = parser.parse_args()

    if not os.path.isfile(args.config_file):
        print('config file {0} not exist'.format(parser.config_file) ,file=sys.stderr)
        exit(1)

    CONFIG = read_json(args.config_file)
    if 'TOKEN_PICKLE_PATH' not in CONFIG:
        print('CONFIG[TOKEN_PICKLE_PATH] not exist' ,file=sys.stderr)
        exit(1)
    TOKEN_PICKLE_PATH=CONFIG['TOKEN_PICKLE_PATH']

    with open(TOKEN_PICKLE_PATH, 'rb') as token:
        creds = pickle.load(token)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PICKLE_PATH, 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    
    result = sheet.values().get(
        spreadsheetId=CONFIG['RESTAURANT_SHEET']['spreadsheet_id'],
        range=CONFIG['RESTAURANT_SHEET']['sheet_name']
    ).execute()
    restaurant_sheet = result.get('values', [])
    
    restautant_col_list = restaurant_sheet[0]
    isActive_idx = restautant_col_list.index('isActive')
    rest_id_idx = restautant_col_list.index('id')
    name_idx = restautant_col_list.index('name')
    phoneNo_idx = restautant_col_list.index('phoneNo')
    address_idx = restautant_col_list.index('address')

    name_to_rest_id_list_dict = {}
    phone_no_to_rest_id_list_dict = {}
    rest_id_to_rest_data_dict = {}
    for restaurant_row in restaurant_sheet[1:]:
        isActive = get_data(restaurant_row,isActive_idx)
        if isActive != 'TRUE': continue

        rest_id = get_data(restaurant_row,rest_id_idx)
        if not rest_id: continue

        name = get_data(restaurant_row,name_idx)
        phoneNo = get_data(restaurant_row,phoneNo_idx)
        address = get_data(restaurant_row,address_idx)

        if name:
            if not name in name_to_rest_id_list_dict:
                name_to_rest_id_list_dict[name] = []
            name_to_rest_id_list_dict[name].append(rest_id)

        phone_no_list = [phoneNo]
        phone_no_list = itertools.chain.from_iterable(map(lambda i:i.split('/'),phone_no_list))
        phone_no_list = itertools.chain.from_iterable(map(lambda i:i.split(','),phone_no_list))
        phone_no_list = map(num_only,phone_no_list)
        phone_no_list = list(phone_no_list)
        for phone_no in phone_no_list:
            if not phone_no: continue
            if not phone_no in phone_no_to_rest_id_list_dict:
                phone_no_to_rest_id_list_dict[phone_no] = []
            phone_no_to_rest_id_list_dict[phone_no].append(rest_id)

        rest_data = {
            'rest_id': rest_id,
            'rest_name': name,
            'rest_phoneNo': phoneNo,
            'rest_address': address,
        }
        rest_id_to_rest_data_dict[rest_id] = rest_data

    #for phone_no, rest_id_list in phone_no_to_rest_id_list_dict.items():
    #    #if len(phone_no) == 8: continue
    #    print('{0}: {1}'.format(phone_no, rest_id_list))

    result = sheet.values().get(
        spreadsheetId=CONFIG['FACT_SHEET']['spreadsheet_id'],
        range=CONFIG['FACT_SHEET']['sheet_name']
    ).execute()
    fact_sheet = result.get('values', [])
    
    fact_col_list = fact_sheet[0]
    timestamp_idx = fact_col_list.index('時間戳記')
    name_idx = fact_col_list.index('商家名稱')
    address_idx = fact_col_list.index('餐廳確實地址（如有）')
    phone_idx = fact_col_list.index('餐廳電話號碼（如有）')

    fact_data_list = []
    fact_row_list = fact_sheet[1:]
    for idx in range(len(fact_row_list)):
        fact_row = fact_row_list[idx]
        fact_data = {
            'fact_row':         idx+2,
            'fact_timestamp':   get_data(fact_row,timestamp_idx),
            'fact_name':        get_data(fact_row,name_idx),
            'fact_address':     get_data(fact_row,address_idx),
            'fact_phone':       get_data(fact_row,phone_idx),
            'rest_id':          '',
        }
        fact_data_list.append(fact_data)

    for fact_data in fact_data_list:
        if fact_data['rest_id']: continue
        fact_phone = fact_data['fact_phone']
        if fact_phone not in phone_no_to_rest_id_list_dict: continue
        rest_id_list = phone_no_to_rest_id_list_dict[fact_phone]
        if len(rest_id_list) == 1:
            fact_data['rest_id'] = rest_id_list[0]
            continue
        if len(rest_id_list) <= 0: continue
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
        fact_data['rest_phoneNo'] = rest_data['rest_phoneNo']
        fact_data['rest_address'] = rest_data['rest_address']

    #write_json('test.json',fact_data_list)

    output_col_list = [
        'fact_row',
        'fact_timestamp',
        'rest_id',
        'fact_name',
        'rest_name',
        'fact_phone',
        'rest_phoneNo',
        'fact_address',
        'rest_address',
    ]

    output_row_list = []
    output_row_list.append(output_col_list)

    for fact_data in fact_data_list:
        row = []
        for col in output_col_list:
            if col in fact_data:
                row.append(fact_data[col])
            else:
                row.append('')
        output_row_list.append(row)

    result = sheet.get(
        spreadsheetId=CONFIG['OUTPUT_SHEET']['spreadsheet_id'],
    ).execute()
    sheet_name_list = [
        sheet['properties']['title']
        for sheet in result['sheets']
    ]
    if CONFIG['OUTPUT_SHEET']['sheet_name'] not in sheet_name_list:
        sheet.batchUpdate(
            spreadsheetId=CONFIG['OUTPUT_SHEET']['spreadsheet_id'],
            body={'requests':[{'addSheet':{'properties':{
                'title':CONFIG['OUTPUT_SHEET']['sheet_name']
            }}}]}
        ).execute()

    update_body ={
        'values': output_row_list,
    }
    sheet.values().update(
        spreadsheetId=CONFIG['OUTPUT_SHEET']['spreadsheet_id'],
        range=CONFIG['OUTPUT_SHEET']['sheet_name'],
        body=update_body,
        valueInputOption='RAW'
    ).execute()
