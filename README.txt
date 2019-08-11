# prepare

Go to https://developers.google.com/sheets/api/quickstart/python
Click the blue "ENABLE THE GOOGLE SHEETS API" button.
Copy the credentials.json file to project root folder.

In Google Sheets, create new spreadsheet
Remember the ID as [OUTPUT_SHEET] .

Copy config.sample.json to config.json.
Modify it.
- FACT_SHEET
- RESTAURANT_SHEET
- OUTPUT_SHEET (as [OUTPUT_SHEET] above)

Bash console:

virtualenv --python python3 pyenv
. pyenv/bin/activate

pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

# login and create token.pickle
python login.py config.json

# output the combine sheet
python combine.py config.json
