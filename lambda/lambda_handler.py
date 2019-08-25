import main
import os

def get_var(key, event):
    return  event[key] if key in event else \
            os.environ[key]

def lambda_handler(event, context):
    print('LFQBSKRZHK')
    spreadsheet_id      = get_var('spreadsheet_id', event)
    sheet_title         = get_var('sheet_title', event)
    token_pickle_url    = get_var('token_pickle_url', event)
    main.main(
        spreadsheet_id      = spreadsheet_id,
        sheet_title         = sheet_title,
        token_pickle_url    = token_pickle_url,
    )
    print('OHDKYGFBDY')
    