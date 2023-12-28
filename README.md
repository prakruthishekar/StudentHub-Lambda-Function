# Serverless Lambda Function for Assignment Submission Notification

This repository contains a serverless AWS Lambda function written in Python. The function gets triggered by an AWS SNS topic and sends out an email notification regarding the submission of assignments received from an API.

## Functionality

The Lambda function is designed to perform the following tasks:
- Listen to an AWS SNS topic for incoming messages related to assignment submissions.
- Receive data about the submission from an API trigger through SNS.
- Compose an email notification summarizing the assignment submission details.
- Send the email notification to designated recipients.

## Setup

### Requirements
- AWS account with necessary permissions to create Lambda functions, SNS topics, and IAM roles.
- Python 3.x installed locally.
- AWS CLI configured with appropriate credentials.

### Deployment Steps
1. Clone this repository to your local machine.

2. Navigate to the project directory:
    ```
    cd lambda-assignment-notification
    ```

3. Set up a virtual environment (optional but recommended):
    ```
    python3 -m venv venv
    source venv/bin/activate
    ```

4. Install required dependencies:
    ```
    pip install boto3  # AWS SDK for Python
    # Other necessary packages
    ```

5. Modify the `lambda_function.py` file to suit your specific requirements. Update the email content, recipients, and any other necessary configurations.

6. Deploy the Lambda function to AWS:
    ```
    aws lambda create-function --function-name AssignmentNotification --runtime python3.8 --role <YOUR-ROLE-ARN> --handler lambda_function.lambda_handler --zip-file fileb://lambda_function.zip
    ```
    Replace `<YOUR-ROLE-ARN>` with the ARN of the IAM role associated with your Lambda function.

7. Create an SNS topic in your AWS account and subscribe the Lambda function to this topic.

8. Trigger the Lambda function by publishing a message to the SNS topic with assignment submission details from your API.

## Usage

To trigger the Lambda function and send an assignment submission notification:
1. Make a POST request to your API endpoint responsible for handling assignment submissions.

2. Once the submission is received by the API, publish a message to the configured SNS topic with the relevant details about the assignment submission.

3. The Lambda function will be triggered by the SNS topic and will send out an email notification based on the provided details.

## Configuration

### Environment Variables
- Modify environment variables within the Lambda function configuration if required, for example:
    - `EMAIL_SENDER`: Email address of the sender.
    - `EMAIL_SUBJECT`: Subject line for the assignment submission notification.
    - `RECIPIENTS`: Email addresses of recipients who should receive the notification.

### IAM Permissions
Ensure the IAM role attached to the Lambda function has appropriate permissions to:
- Publish and receive messages from the configured SNS topic.
- Send emails using AWS SES (Simple Email Service) or other email sending services configured.

## Notes
- Update the IAM role permissions and AWS configurations based on your specific setup and security requirements.
- Monitor AWS costs associated with using Lambda, SNS, and other related services.

