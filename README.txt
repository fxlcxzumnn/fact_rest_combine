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

MAIN_PWD=${PWD}

sudo apt-get install python3-venv

# Create venv for development
rm -rf venv_dev
python3 -m venv venv_dev
source venv_dev/bin/activate
pip install --upgrade wheel google-api-python-client google-auth-httplib2 google-auth-oauthlib boto3 pytz

# exit venv
deactivate

# Create venv for AWS upload
rm -rf venv_aws
python3 -m venv venv_aws
source venv_aws/bin/activate
pip install --upgrade awscli

# Create upload package
cd ${MAIN_PWD}/lambda
rm -f ${MAIN_PWD}/lambda.zip
cd ${MAIN_PWD}/venv_dev/lib/python3.7/site-packages
zip -r9 ${MAIN_PWD}/lambda.zip .
cd ${MAIN_PWD}/lambda
zip -g ${MAIN_PWD}/lambda.zip google_sheet.py
zip -g ${MAIN_PWD}/lambda.zip lambda_handler.py
zip -g ${MAIN_PWD}/lambda.zip main.py

# Create new lambda function
cd ${MAIN_PWD}
aws lambda create-function \
    --function-name freedomhi_fact_rest_combine \
    --runtime python3.7 \
    --role arn:aws:iam::892038990546:role/aws-lambda-execute \
    --handler lambda_handler.lambda_handler \
    --zip-file fileb://lambda.zip \
    --profile fxl \
    --region us-east-2

# Update lambda function
cd ${MAIN_PWD}
aws lambda update-function-code \
    --function-name freedomhi_fact_rest_combine \
    --zip-file fileb://lambda.zip \
    --profile fxl \
    --region us-east-2

# exit venv
deactivate

