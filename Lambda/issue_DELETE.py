import json
import boto3

def bad_request_not_found(key):
    return {
    'statusCode': 400,
        "headers": {
            "Content-Type": "application/json"
        },
        'body': json.dumps({
            'message': str(key) + " not found in request body."
        })
    }
  
ISSUE_TABLE = "IssueListening"
def lambda_handler(event, context):
    if event.get("issueUrl") == None:
        return bad_request_not_found("issueUrl")
    print(event["issueUrl"])
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(ISSUE_TABLE)
    try:
        response = table.delete_item(Key={"issueUrl": event["issueUrl"]})
        return response
    except:
        return{
            'statusCode': 400,
            'body': None
        }