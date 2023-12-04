import boto3
import requests
from google.cloud import storage
from google.oauth2 import service_account
import json
import os
import logging
import base64
import datetime
import smtplib
import zipfile
import io
from email.mime.text import MIMEText

def lambda_handler(event, context):

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Extract submission URL and user email from the SNS message
    message_str = event['Records'][0]['Sns']['Message']
    logger.info("message_str: %s", message_str)

    # Parse the message string as JSON
    message = json.loads(message_str)
    logger.info("message: %s", message)

    # Extract submission_url and user_email
    # status=message['status']
    submission_url = message['submission_url']
    user_email = message['user_email']
    assignment_id = message['assignment_id']
    # account_id = message['account_id']
    first_name = message['first_name']
    last_name = message['last_name']
    # attempt = message['attempt']
    logger.info("submission_url: %s", submission_url)
    logger.info("user_email: %s", user_email)
    logger.info("assignment_id: %s", assignment_id)

    # Download the submission from the submission_url
    response = requests.get(submission_url)


    google_creds_base64 = os.environ['GOOGLE_CREDENTIALS']
    google_creds_json = base64.b64decode(google_creds_base64).decode('utf-8')

    try:
        # Parse the JSON string into a dictionary
        google_creds = json.loads(google_creds_json)
    except json.JSONDecodeError as e:
        print("Error parsing JSON: ", e)
        logger.info("Error " + e)
        print("JSON string: ", google_creds_json)
        logger.info("GOOGLE_CREDENTIALS: JSON " + google_creds_json)
        raise

    # Google Cloud authentication
    credentials = service_account.Credentials.from_service_account_info(google_creds)
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(os.environ.get('BUCKET_NAME'))
    logger.info("GCP_BUCKET_NAME: " + os.environ.get('BUCKET_NAME'))
    source_email = "mailgun@prakruthi.me"

    logger.info("source_email : %s", source_email)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    response = requests.get(submission_url)
    file_content = response.content
    directory_path = f"{user_email}/{assignment_id}/"
    unique_file_name = f"submission_{timestamp}.zip"
    full_path = directory_path + unique_file_name

    # Check if the request was successful
    if response.status_code == 200:
        # Process the file and upload to GCP
        
        blob = bucket.blob(full_path)
        blob.upload_from_string(file_content)
        logger.info("Full_path : %s", full_path)
        
        
        # Use BytesIO to handle the downloaded content as a file-like object
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))

        # Check if the ZIP file is empty or contains empty folders
        if not zip_file.namelist():
            print("The ZIP file is empty.")
            # Handle empty file scenario
            logger.warning("Empty file submitted")
            send_email(os.environ.get("MAILGUN_DOMAIN"), user_email, first_name, last_name, submission_url, assignment_id, source_email, "Submission Error",
                        f"Error occurred while downloading the file: Empty folder" , full_path, timestamp, response.status_code)
            update_dynamodb(user_email, assignment_id, submission_url, timestamp,"Failed", "Empty file submitted")
            logger.info("Updating dynamo DB, status-failure")
            # handle_empty_file_scenario(user_email, submission_url, assignment_id)
        else:
            is_empty = all([zip_info.filename.endswith('/') for zip_info in zip_file.infolist()])
            if is_empty:
                print("The ZIP file contains only empty folders.")
                # Handle errors during download
                logger.error(f"The ZIP file contains only empty folders.")
                logger.info("Sending Email")
                send_email(os.environ.get("MAILGUN_DOMAIN"), user_email, first_name, last_name, submission_url, assignment_id, source_email, "Download Failed",
                                f"The ZIP file contains only empty folders. " , full_path, timestamp, response.status_code)

                update_dynamodb(user_email, assignment_id, submission_url, timestamp, "Failed", "Download error")
                logger.info("Updating dynamo DB, status-failure")      
    
            else:
                print("The ZIP file contains files.")
                # Send success email
                send_email(os.environ.get("MAILGUN_DOMAIN"), user_email, first_name, last_name, submission_url, assignment_id, source_email, "Submission Submitted Successfully - Canvas",
                            "We are pleased to inform you that your submission for the assignment and has been successfully received and processed." , full_path, timestamp, response.status_code)
                update_dynamodb(user_email, assignment_id, submission_url, timestamp,"Success", "Assignment Submitted")
                logger.info("Updating dynamo DB, status-success")
                logger.info("Table updated")

    else:
        # Handle errors during download
        logger.error(f"Error occurred while downloading the file:")
        send_email(os.environ.get("MAILGUN_DOMAIN"), user_email, first_name, last_name, submission_url, assignment_id, source_email, "Download Failed",
                        f"Error occurred while downloading the file: " , full_path, timestamp, response.status_code)

        update_dynamodb(user_email, assignment_id, submission_url, timestamp, "Failed", "Download error")
        logger.info("Updating dynamo DB, status-failure")      
    


def send_email(domain, user_email, first_name, last_name, submission_url, assignment_id, source_email, subject, body, full_path, timestamp, code):
    print("Sending email ", user_email, submission_url, assignment_id, source_email, subject, body)
    # Mailgun parameters
    logger = logging.getLogger()
    api_key = os.environ.get('MAILGUN_API_KEY')
    to_address = user_email

    email_body = "\r\n" + "Dear "+first_name +" "+last_name+",\r\n" + body + "\r\n" + "- Assignment ID: "+ assignment_id + "\r\n" + "- Submission URL: " + submission_url + "\r\n" + "- Status Code: "+ str(code) + "\r\n" + "\r\n\r\n" + "Should you have any questions or need further assistance, please feel free to contact us at info@prakruthi.me.\r\n\r\nWe appreciate your effort and time.\r\n\r\nBest regards,\r\nCanvas\r\n"
    

    url = f"https://api.mailgun.net/v3/{domain}/messages"
    auth = ('api', api_key)
    data = {'from': f'Lambda Function <mailgun@{domain}>',
            'to': user_email,
            'subject': subject,
            'text': email_body}
    
    try:
        response = requests.post(url, auth=auth, data=data)
        response.raise_for_status()
        logger.info(f"Email sent successfully to {to_address}")

    except requests.RequestException as e:
        # Track failed email in DynamoDB
        pass
        # update_dynamodb(user_email, assignment_id, submission_url, full_path, timestamp, "Failure")


def update_dynamodb(user_email, assignment_id, submission_url, timestamp, status, message):
    table_name = os.environ.get('DYNAMODB_TABLE')
    partition_key = f"{user_email}#{assignment_id}#{timestamp}"
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    table.put_item(
        Item={
            'id': partition_key,
            'AssignmentId': assignment_id,
            'SubmissionUrl': submission_url,
            'Timestamp':  timestamp,
            "Status": status,
            "Message": message
        }
    )


