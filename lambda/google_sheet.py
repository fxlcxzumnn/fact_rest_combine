import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def to_value_itr(value_list, length):
    ret_value_itr = range(length)
    ret_value_itr = map(lambda i: to_value(value_list, i), ret_value_itr)
    return ret_value_itr

def to_value(value_list, idx):
    return value_list[idx] if idx < len(value_list) else ''

def value_list_list_to_value_dict_list(value_list_list):
    col_list = value_list_list[0]
    value_dict_list = [
        {
            col_list[col_idx] : value_list[col_idx]
            for col_idx in range(len(col_list))
        }
        for value_list in value_list_list[1:]
    ]
    return value_dict_list, col_list

def value_dict_list_to_value_list_list(value_dict_list, col_list=None):
    if col_list is None:
        col_set = set()
        for value_dict in value_dict_list:
            for k in value_dict:
                col_set.add(k)
        col_list = list(sorted(col_set))
    value_list_list = [
        [
            value_dict[col] if col in value_dict else ''
            for col in col_list
        ]
        for value_dict in value_dict_list
    ]
    return [col_list] + value_list_list

def value_list_list_to_dict(value_list_list):
    return {
        value_list[0]: value_list[1]
        for value_list in value_list_list
        if value_list[0]
    }

def dict_to_value_list_list(ddict):
    return [
        [k, ddict[k]]
        for k in sorted(ddict)
    ]

def get_value_list_list(
        spreadsheet_id, sheet_title,
        spreadsheets,
    ):
    #print('WAEGIRIGYT')

    get_result = spreadsheets.values().get(
        spreadsheetId=spreadsheet_id,
        range=sheet_title,
    ).execute()
    value_list_list = get_result.get('values', [])
    
    #print('VVGAOZZYKO')
    col_count_list = map(len, value_list_list)
    max_col_count = max(col_count_list)

    value_list_list = map(lambda i:to_value_itr(i, max_col_count), value_list_list)
    value_list_list = map(list, value_list_list)
    value_list_list = list(value_list_list)
    
    return value_list_list

def set_value_list_list(
        spreadsheet_id, sheet_title,
        value_list_list,
        spreadsheets,
    ):
    update_body ={
        'values': value_list_list,
    }
    update_range = "'{sheet_title}'".format(sheet_title=sheet_title)
    spreadsheets.values().update(
        spreadsheetId       = spreadsheet_id,
        range               = update_range,
        body                = update_body,
        valueInputOption    = 'RAW',
    ).execute()

def get_sheet_title_list(spreadsheet_id, spreadsheets):
    result = spreadsheets.get(spreadsheetId=spreadsheet_id).execute()
    sheet_title_list = [
        sheet['properties']['title']
        for sheet in result['sheets']
    ]
    return sheet_title_list

def add_sheet(spreadsheet_id, sheet_title, spreadsheets):
    spreadsheets.batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests':[{'addSheet':{'properties':{
            'title':sheet_title
        }}}]}
    ).execute()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Google sheet to csv/json')
    parser.add_argument('spreadsheet_id', type=str)
    parser.add_argument('sheet_title', type=str)
    parser.add_argument('token_pickle', type=str)
    parser.add_argument('--csv_output')
    parser.add_argument('--json_output')
    parser.add_argument('--dict_output')
    parser.add_argument('--csv_input')
    parser.add_argument('--json_input')
    parser.add_argument('--dict_input')
    args = parser.parse_args()
    
    with open(args.token_pickle, 'rb') as token:
        creds = pickle.load(token)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build('sheets', 'v4', credentials=creds)
    spreadsheets = service.spreadsheets()

    if args.csv_output or args.json_output or args.dict_output:
        value_list_list = get_value_list_list(
            spreadsheet_id  = args.spreadsheet_id,
            sheet_title     = args.sheet_title,
            spreadsheets    = spreadsheets,
        )
        #print(value_list_list)
    
    if args.csv_output:
        import csv
        with open(args.csv_output,'w') as fout:
            csv_out = csv.writer(fout)
            for value_list in value_list_list:
                csv_out.writerow(value_list)

    if args.json_output:
        import json
        value_dict_list, _ = value_list_list_to_value_dict_list(value_list_list)
        with open(args.json_output,'w') as fout:
            json.dump(value_dict_list,fout,sort_keys=True,indent=2,ensure_ascii=False)
            fout.write('\n')
    
    if args.dict_output:
        import json
        ddict = value_list_list_to_dict(value_list_list)
        with open(args.dict_output,'w') as fout:
            json.dump(ddict,fout,sort_keys=True,indent=2,ensure_ascii=False)
            fout.write('\n')

    if args.csv_input or args.json_input or args.dict_input:
        sheet_title_list = get_sheet_title_list(
            spreadsheet_id  = args.spreadsheet_id,
            spreadsheets    = spreadsheets,
        )
        if args.sheet_title not in sheet_title_list:
            add_sheet(
                spreadsheet_id  = args.spreadsheet_id,
                sheet_title     = args.sheet_title,
                spreadsheets    = spreadsheets,
            )

    value_list_list = None
    if args.csv_input:
        value_list_list = []
        import csv
        with open(args.csv_input,'r') as fin:
            for row in csv.reader(fin):
                value_list_list.append(row)
    elif args.json_input:
        import json
        with open(args.json_input,'r') as fin:
            value_dict_list = json.load(fin)
        value_list_list = value_dict_list_to_value_list_list(value_dict_list)
    elif args.dict_input:
        import json
        with open(args.dict_input,'r') as fin:
            value_dict = json.load(fin)
        value_list_list = dict_to_value_list_list(value_dict)

    if value_list_list:
        set_value_list_list(
            spreadsheet_id  = args.spreadsheet_id,
            sheet_title     = args.sheet_title,
            value_list_list = value_list_list,
            spreadsheets    = spreadsheets,
        )
