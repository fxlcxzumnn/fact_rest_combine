# prepare

Prepare AWS account

Go to https://developers.google.com/sheets/api/quickstart/python
Click the blue "ENABLE THE GOOGLE SHEETS API" button.
Copy the credentials.json file to project root folder.

##############################

AWS_PROFILE=xxx         # As you like
AWS_REGION=us-east-2    # As you like
MAIN_PWD=${PWD}         # Project root folder, contains this README.txt

sudo apt-get install python3-venv

# Create venv for development
cd ${MAIN_PWD}
rm -rf venv_dev
python3 -m venv venv_dev
source venv_dev/bin/activate
pip install --upgrade wheel google-api-python-client google-auth-httplib2 google-auth-oauthlib boto3 pytz

# Create login token
cd ${MAIN_PWD}
python3 login.py credentials.json token.pickle

# exit venv
deactivate

# Create venv for AWS upload
cd ${MAIN_PWD}
rm -rf venv_aws
python3 -m venv venv_aws
source venv_aws/bin/activate
pip install --upgrade awscli

# Create upload package
rm -rf ${MAIN_PWD}/build
mkdir ${MAIN_PWD}/build
cd ${MAIN_PWD}/venv_dev/lib/python3.7/site-packages
zip -r9 ${MAIN_PWD}/build/lambda.zip .
cd ${MAIN_PWD}/lambda
zip -g ${MAIN_PWD}/build/lambda.zip google_sheet.py
zip -g ${MAIN_PWD}/build/lambda.zip lambda_handler.py
zip -g ${MAIN_PWD}/build/lambda.zip main.py

# Create new lambda function
cd ${MAIN_PWD}
aws lambda create-function \
    --function-name freedomhi_fact_rest_combine \
    --runtime python3.7 \
    --role arn:aws:iam::892038990546:role/aws-lambda-execute \
    --handler lambda_handler.lambda_handler \
    --zip-file fileb://build/lambda.zip \
    --profile ${AWS_PROFILE} \
    --region ${AWS_REGION}

# Update lambda function
cd ${MAIN_PWD}
aws lambda update-function-code \
    --function-name freedomhi_fact_rest_combine \
    --zip-file fileb://build/lambda.zip \
    --profile ${AWS_PROFILE} \
    --region ${AWS_REGION}

# exit venv
deactivate

##############################

In Google Sheets, import param.sample.csv.
Modify [ FILL ME ] part.
Remember it's Sheet ID as [GOOGLE_SHEET_ID]
Remember it's Sheet name as [GOOGLE_SHEET_NAME]

Upload token.pickle to S3
Remember it's s3 path (s3://xxx/xxx) as [TOKEN_PICKLE_S3_URL]

Go to AWS Lambda console
https://us-east-2.console.aws.amazon.com/lambda/home
Choose correct region
Go to lambda function

Add environment variables:
spreadsheet_id:   ( fill [GOOGLE_SHEET_ID] )
sheet_title:      ( fille [GOOGLE_SHEET_NAME] )
token_pickle_url: ( fill [TOKEN_PICKLE_S3_URL] )

Basic settings:
Memory: 256 MB, I have tried 128MB, then it run super slow
Timeout: 1 min, My function run 23sec.

Create Lambda test, event content as empty {}.
Run the test.
The sheet in [GOOGLE_SHEET_ID]'s output_xxx and var_xxx should be updated.

Create CloudWatch Events for hourly schedule task.
> Click "Add trigger"
> "CloudWatch Events"
> "Rule" = "Create a new rule"
> Fill "Rule name"
> "Rule type" = "Schedule expression"
> "Schedule expression" = "rate(1 hour)"
> "Enable trigger" = "YES"
> Click "Add"

The Google sheet will be updated per hour.
Everything done and nice.
