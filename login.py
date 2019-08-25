import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
import argparse

def read_json(fn):
    with open(fn,'r') as fin:
        return json.load(fin)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Combine fact and restaurant data')
    parser.add_argument('credentials_path', type=str)
    parser.add_argument('token_pickle_path', type=str)
    args = parser.parse_args()

    if not os.path.isfile(args.credentials_path):
        print('credentials file {0} not exist'.format(parser.credentials_path) ,file=sys.stderr)
        exit(1)

    CREDENTIALS_PATH=args.credentials_path
    TOKEN_PICKLE_PATH=args.token_pickle_path
    SCOPES=['https://www.googleapis.com/auth/spreadsheets']
    
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save the credentials for the next run
    with open(TOKEN_PICKLE_PATH, 'wb') as token:
        pickle.dump(creds, token)
