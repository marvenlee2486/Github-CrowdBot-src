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
    # if event.get("chatId") == None:
    #     return bad_request_not_found("chatId")
    if event.get("issueUrl") == None:
        return bad_request_not_found("issueUrl")
    print(event["issueUrl"])
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(ISSUE_TABLE)
    response = table.get_item(Key={"issueUrl": event["issueUrl"]})
    try:
        chatId = response["Item"]["chatId"]
        return {
            'statusCode': 200,
            'body': chatId
        }
    except:
        return{
            'statusCode': 200,
            'body': None
        }