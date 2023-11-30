import base64
import json
import logging
import requests
import os
from google.cloud import storage
import boto3
from google.oauth2 import service_account

# def lambda_handler(event, context):

#     logger = logging.getLogger()
#     logger.setLevel(logging.INFO)
    
#     print("Received event:", json.dumps(event, indent=2))
#     # Assuming the first record's message is what you need
#     # Extracting the SNS message and parsing it as JSON
#     sns_message_str = event['Records'][0]['Sns']['Message']
#     sns_message = json.loads(sns_message_str)
    
#     # Now you can use sns_message as needed
#     print("Received SNS message:", sns_message)
#     recipient = sns_message["user"]
#     github_url = sns_message["url"]

#     mailgun_api_key = os.environ.get('MAILGUN_API_KEY')
#     mailgun_domain = os.environ.get("MAILGUN_DOMAIN")  # Replace with your Mailgun domain
#     recipient = "prakruthisomashekar29@gmail.com"  # Replace with the recipient's email address
#     subject = "Hello from Lambda!"
#     body = "This is a test email sent from an AWS Lambda function using Mailgun."


#     # Download the file from GitHub
#     try:
#         download_response = requests.get(github_url)
#         download_response.raise_for_status()  # Raise an error for bad responses

#         # Check if the file is not empty
#         if download_response.content:
#             # Store in Google Cloud Storage
#             store_in_gcs(download_response.content, os.environ.get('BUCKET_NAME'), "webapp-assignment.zip")

#             # Email the user about successful download
#             send_email(os.environ.get('MAILGUN_API_KEY'), os.environ.get("MAILGUN_DOMAIN"), 
#                        recipient, "Download Successful", "Your file has been downloaded successfully.")
#         else:
#             # Handle empty file scenario
#             send_email(os.environ.get('MAILGUN_API_KEY'), os.environ.get("MAILGUN_DOMAIN"), 
#                        recipient, "Download Failed", "The file was empty.")
        
#     except requests.RequestException as e:
#         # Handle errors during download
#         send_email(os.environ.get('MAILGUN_API_KEY'), os.environ.get("MAILGUN_DOMAIN"), 
#                    recipient, "Download Failed", f"Error occurred while downloading the file: {e}")
        
#     # send_email(mailgun_api_key, mailgun_domain, recipient, subject, body)
    


# def store_in_gcs(file_content, bucket_name, file_name):
#     # Parse the credentials from the environment variable
#     credentials_info_str = os.environ.get('GOOGLE_CREDENTIALS')
#     google_creds_json = base64.b64decode(credentials_info_str).decode('utf-8')
    
#     try:
#         # Parse the JSON string into a dictionary
#         google_creds = json.loads(google_creds_json)
#     except json.JSONDecodeError as e:
#         print("Error parsing JSON: ", e)
#         logger.info("Error " + e)
#         print("JSON string: ", google_creds_json)
#         logger.info("GOOGLE_CREDENTIALS: JSON " + google_creds_json)
#         raise

#     print("Type of credentials_info:", type(credentials_info_str))
#     print("Content of credentials_info:", credentials_info_str)
#     credentials = service_account.Credentials.from_service_account_info(credentials_info)

#     # Initialize the storage client with the credentials
#     storage_client = storage.Client(credentials=credentials)
#     bucket = storage_client.bucket(bucket_name)
#     blob = bucket.blob(file_name)
#     blob.upload_from_string(file_content)
#     print("File Uploaded to S3")


# def send_email(api_key, domain, recipient, subject, body):
#     url = f"https://api.mailgun.net/v3/{domain}/messages"
#     auth = ('api', api_key)
#     data = {'from': f'Lambda Function <mailgun@{domain}>',
#             'to': recipient,
#             'subject': subject,
#             'text': body}
    
    # try:
    #     response = requests.post(url, auth=auth, data=data)
    #     response.raise_for_status()
    #     # Track successful email in DynamoDB
    #     track_email_status(recipient, "Success", "Email sent successfully")
    # except requests.RequestException as e:
    #     # Track failed email in DynamoDB
    #     track_email_status(recipient, "Failed", str(e))

# def track_email_status(email, status, message):
#     dynamodb = boto3.resource('dynamodb')
#     table = dynamodb.Table(os.environ.get("DYNAMODB_TABLE"))
#     table.put_item(
#         Item={
#             'email': email,
#             'status': status,
#             'message': message
#         }
#     )




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



    response = requests.get(submission_url)
    file_content = response.content
    if response.status_code != 200 or not file_content:
        raise ValueError("Invalid URL or empty content")


    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    directory_path = f"{user_email}/{assignment_id}/"
    unique_file_name = f"submission_{timestamp}.zip"
    full_path = directory_path + unique_file_name
    blob = bucket.blob(full_path)
    blob.upload_from_string(file_content)
    logger.info("full_path : %s", full_path)


    logger.info("Sending Email")
    # Send success email
    send_email(os.environ.get("MAILGUN_DOMAIN"), user_email, first_name, last_name, submission_url, assignment_id, source_email, "Submission Submitted Successfully - Canvas",
                "We are pleased to inform you that your submission for the assignment and has been successfully received and processed." , full_path, timestamp)

    send_emaill(os.environ.get('MAILGUN_API_KEY'), os.environ.get("MAILGUN_DOMAIN"), 
                   "prakruthisomashekar29@gmail.com", "Download Failed", f"Error occurred while downloading the file: {e}")
    logger.info("Email Sent and updating dynamo DB")
    

    logger.info("Table updated")
       

    # except Exception as e:
    #     logger.error(f"Error in processing submission: {e}")
    #     send_email(os.environ.get("MAILGUN_DOMAIN"),user_email, submission_url, assignment_id, source_email, "Submission Error - Canvas",
    #                "There was an error with your submission. Please ensure the URL is correct and the content is not empty.")


def send_email(domain, user_email, first_name, last_name, submission_url, assignment_id, source_email, subject, body, full_path, timestamp):
    print("Sending email ", user_email, submission_url, assignment_id, source_email, subject, body)
    # Mailgun parameters
    logger = logging.getLogger()
    api_key = os.environ.get('MAILGUN_API_KEY')
    to_address = user_email

    email_body = "\r\n" + "Dear "+first_name +" "+last_name+",\r\n" + body + "\r\n" + "- Assignment ID: "+ assignment_id + "\r\n" + "- Submission URL: " + submission_url + "\r\n\r\n" + "Should you have any questions or need further assistance, please feel free to contact us at info@pranaykasavaraju.me.\r\n\r\nWe appreciate your effort and time.\r\n\r\nBest regards,\r\nCanvas\r\n"
    

    url = f"https://api.mailgun.net/v3/{domain}/messages"
    auth = ('api', api_key)
    data = {'from': f'Lambda Function <mailgun@{domain}>',
            'to': "prakruthisomashekar29@gmmail.com",
            'subject': subject,
            'text': email_body}
    
    try:
        response = requests.post(url, auth=auth, data=data)
        response.raise_for_status()
        logger.info(f"Email sent successfully to {to_address}")
        logger.info(f"Email sent successfully to Prakruthi")

        # Update DynamoDB
        update_dynamodb(user_email, assignment_id, submission_url, full_path, timestamp, "Success")
        
    except requests.RequestException as e:
        # Track failed email in DynamoDB
        update_dynamodb(user_email, assignment_id, submission_url, full_path, timestamp, "Failure")
        



def update_dynamodb(user_email, assignment_id, submission_url, full_path, timestamp, status):
    table_name = os.environ.get('DYNAMO_TABLE_NAME')
    partition_key = f"{user_email}#{assignment_id}#{timestamp}"
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    table.put_item(
        Item={
            'ID': partition_key,
            'AssignmentId': assignment_id,
            'SubmissionUrl': submission_url,
            'FilePath': full_path,
            'Timestamp':  timestamp,
            "Status": status
        }
    )


def send_emaill(api_key, domain, recipient, subject, body):
    url = f"https://api.mailgun.net/v3/{domain}/messages"
    auth = ('api', api_key)
    data = {'from': f'Lambda Function <mailgun@{domain}>',
            'to': recipient,
            'subject': subject,
            'text': body}
    
    try:
        response = requests.post(url, auth=auth, data=data)
        response.raise_for_status()
        # Track successful email in DynamoDB
        # track_email_status(recipient, "Success", "Email sent successfully")
    except requests.RequestException as e:
        # Track failed email in DynamoDB
        # track_email_status(recipient, "Failed", str(e))
        pass