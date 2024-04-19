
import json
from http import HTTPStatus
import sys
import pandas as pd
import boto3
import operator 
CHAT_TABLE = "ChatRecord"

def bad_request_not_found(key):
    return {
    'statusCode': HTTPStatus.BAD_REQUEST.value,
        "headers": {
            "Content-Type": "application/json"
        },
        'body': json.dumps({
            'message': str(key) + " not found in request body."
        })
    }

def getExistingChat(chat_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(CHAT_TABLE)
    response = table.query(
        KeyConditionExpression='chatId = :chat_id',
        ExpressionAttributeValues={
            ':chat_id': chat_id
        }
    )
    # Extract items from the response
    items = response.get('Items', [])
    return items
prompt = \
    "This model is tasked with analyzing a C++, SQL, Java code language which focus in cloud security  identify security vulnerabilities. "\
    "The input of the model will be stricly code text." \
    "After examining the code, it will determine whether a fix is required. If a fix is deemed necessary, "\
    "the model will provide reasoning and suggest a ammended code in the same programming language." \
    "Each response should be in the following format:\n\n"\
    "```isFixNecessary\n-----------\n$boolean result (true / false)\n-----------\n\n "\
    "reasoning\n-----------\nreasoning_goes_here\n-----------\n\n "\
    "ammended code\n-----------\n$ammended_code_goes_here\n-----------\n```\n\n "\
    "Follow this format strictly. Do not say anything else. Please do not add comments in the ammended_code."

system_message = \
    "Given a piece of C++, SQL, or Java code focused on cloud security, analyze the code for security vulnerabilities." \
    "If a fix is necessary, provide reasoning and suggest an amended code in the same programming language."
    
def lambda_handler(event, context):
    print(str(event))
    if "chatId" not in event.keys():
        return bad_request_not_found("chatId")
    try:
        chat_id = event['chatId']
        existingChat = getExistingChat(chat_id)
        sorted_list = sorted(existingChat, key=operator.itemgetter('seqId'))
        messages = [
            {
                "role": "system",
                "content": system_message + prompt,
            }]
        for entry in sorted_list:
            messages += [{
                "role": "user",
                "content": entry["user_input"]
            },
            {
                "role": "assistant",
                "content": json.dumps(entry["AI_output"])
            }]
        return {
            'statusCode': 200,
            'body': json.dumps(messages)
        }
    except Exception as e:
        return{
                "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
                "headers": {
                    "Content-Type": "application/json"
                },
                "message": str(e)
            }
