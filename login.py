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
    parser.add_argument('config_file', type=str, help='config file')
    args = parser.parse_args()

    if not os.path.isfile(args.config_file):
        print('config file {0} not exist'.format(parser.config_file) ,file=sys.stderr)
        exit(1)

    config = read_json(args.config_file)
    if 'CREDENTIALS_PATH' not in config:
        print('config[CREDENTIALS_PATH] not exist' ,file=sys.stderr)
        exit(1)
    if 'TOKEN_PICKLE_PATH' not in config:
        print('config[TOKEN_PICKLE_PATH] not exist' ,file=sys.stderr)
        exit(1)

    CREDENTIALS_PATH=config['CREDENTIALS_PATH']
    TOKEN_PICKLE_PATH=config['TOKEN_PICKLE_PATH']
    SCOPES=['https://www.googleapis.com/auth/spreadsheets']
    
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save the credentials for the next run
    with open(TOKEN_PICKLE_PATH, 'wb') as token:
        pickle.dump(creds, token)
