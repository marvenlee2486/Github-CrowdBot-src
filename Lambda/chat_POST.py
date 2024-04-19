
import json
import sys
from openai import OpenAI
import pydantic_core
import pandas as pd
import boto3
import operator

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

system_message = \
  "Given a piece of C++, SQL, or Java code focused on cloud security, analyze the code for security vulnerabilities." \
  "If a fix is necessary, provide reasoning and suggest an amended code in the same programming language."\
  "Use json as output with the following key."\
  "\t title: $Title_of_the_issue,"\
  "\t isFixNecessary: $boolean result (\"true\" / \"false\"),"\
  "\t reasoning: $reason_of_the_fix,"\
  "\t ammended code: $suggested_ammended_code"
  
  
API_KEY = "OPEN_AI_API"
JOB_ID = "JOB_ID"
CHAT_TABLE = "ChatRecord"

def new_chat(content, old_content):
    print(content)
    temperature = 0
    
    client = OpenAI(api_key=API_KEY)
    model_name_pre_object = client.fine_tuning.jobs.retrieve(JOB_ID)
    model_name = model_name_pre_object.fine_tuned_model
    
    sorted_list = sorted(old_content, key=operator.itemgetter('seqId'))
    messages = [
        {
            "role": "system",
            "content": system_message # + prompt,
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
    messages += [{
      "role": "user",
      "content": content,
    }]
    
    # # messages[1]['content'] = prompt + messages[1]['content']
    # if len(messages) > 2:
    #     print("USE CONVERSATIONAL")
    #     model_name = "gpt-4-turbo-preview"
    #     messages[-1]['content'] = 
    print(messages)
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=2000,
        response_format={ "type": "json_object" }
    )
    
    print(response)
    output = response.choices[0].message.content
    print(output)
    json_output = json.loads(output)
    return output
        
def add_new_chat_to_db(chat_id, user_chat, AI_chat, seqId = 1):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(CHAT_TABLE)
    table.put_item(
        Item = {
            "seqId":seqId,
            "chatId":chat_id,
            "user_input":user_chat,
            "AI_output":AI_chat,
        })
    return chat_id
    

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

def lambda_handler(event, context):
    print(str(event))
    if "code" not in event.keys():
        return bad_request_not_found("code")
    if "chatId" not in event.keys():
        return bad_request_not_found("chatId")
    try:
        chat_id = event['chatId']
        code = event['code']
        existingChat = getExistingChat(chat_id)
        reply = new_chat(code, existingChat)
        chatId = add_new_chat_to_db(chat_id, code, json.dumps(reply), len(existingChat) + 1)
        return {
            'statusCode': 200,
            'body': json.dumps(reply)
        }
    except Exception as e:
        return{
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json"
                },
                "message": str(e)
            }

