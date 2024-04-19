from flask import Flask, request, jsonify
import json
import requests


API = "https://osux3ugujk.execute-api.ap-southeast-1.amazonaws.com/deploy/"
CHAT_API = API + "chat"
ISSUE_API = API + "issue"
GITHUB_API_KEY = "==GITHUB-API-KEY=="

def form_the_reply(reply, path = None):
    try:
        if path is None:
           formatted_reply = "## Reasoning\n" + reply["reasoning"] + "\n ## Suggested Amended Code\n ``` \n" + reply["ammended code"] + "\n ``` "
        else:
            formatted_reply = "## Suggested Code changes\n " + path + "\n## Reasoning\n" + reply["reasoning"] + "\n ## Suggested Amended Code\n ``` \n" + reply["ammended code"] + "\n ``` "
        return formatted_reply
    except Exception as e:
        print(e)
        return json.dumps(reply)
    
app = Flask(__name__)
def process_issue(commit_obj):
    if commit_obj["sender"]["login"] == "Gitchatbot":
        return  
    content_body = { "issueUrl":  commit_obj["issue"]["url"]}
    content_hash = requests.get(ISSUE_API, data = json.dumps(content_body)).json()["body"]
    print(content_hash)
    if content_hash == None:
        return 
    
    comment = commit_obj["comment"]["body"]
    if commit_obj["issue"]["state"] == "closed":
        requests.delete(ISSUE_API, data = json.dumps(content_body))
        return
    data = {"chatId": content_hash, "code": comment}
                    
    res = requests.post(CHAT_API, data = json.dumps(data))
    print(res.text)
    reply = json.loads(res.json()['body'])
    reply = json.loads(reply)
    comments_url = commit_obj["issue"]["comments_url"]
    headers = {"Accept":"application/vnd.github+json", "Authorization": "Bearer " + GITHUB_API_KEY}
    res = requests.post(comments_url, headers = headers , json = {"body": form_the_reply(reply)})
    print(res)
    print(res.text)


def create_issue(commit_obj, res, hash, content_url):
    # print(commit_obj, res, hash ) 
    print(res)
    res = json.loads(res)
    
    if str(res["isFixNecessary"])[0] == "f":
        return 
    if str(res["isFixNecessary"])[0] == "F":
        return 
    issue_url = commit_obj["repository"]["issues_url"]

    title = res['title']

    content_body = {
        "title": title, 
        "body": form_the_reply(res, content_url)
    }
    headers = {"Accept":"application/vnd.github+json", "Authorization": "Bearer " + GITHUB_API_KEY}
    res = requests.post(issue_url.replace("{/number}",""), headers = headers , json = content_body)
    if res.status_code != 201:
        print("issue Create fail", content_body, headers)
        return 
    url = res.json()["url"]
    content_body = {    
                    "issueUrl": url,
                    "chatId": hash
                    }
    response = requests.post(ISSUE_API, data = json.dumps(content_body))
    print(response.text)
    res.json()
    

def process_push(commit_obj):
    ref = "refs/heads/" + commit_obj["repository"]["master_branch"]
    print(ref)
    if commit_obj["ref"] != ref:
        return
    print("OK")
    content_api = commit_obj["repository"]["contents_url"]

    for commit in commit_obj['commits']:
        added = commit["added"]
        modified = commit["modified"]
        modified_files = added + modified
        
        for file in modified_files:
            content_url = content_api.replace("{+path}",file)
            print(content_url)
            
            # Send a get request 
            response = requests.get(content_url)
            if response.ok:
                content_obj = response.json()
                # print(content_obj.keys())
                # print(content_obj)
                content_hash = content_obj['sha']
                download_url = content_obj['download_url']

                ## TODO if content hash is found id ChatRecord, continue
                # if content_hash 
                # Send another get request to get the content
                response = requests.get(download_url)
                if response.ok:
                    source_code = response.text
                    # print(source_code)   
                    data = {"chatId": content_hash, "code": source_code}
                    res = requests.post(CHAT_API, data = json.dumps(data))
                    #print(res.json())
                    reply = json.loads(res.json()['body'])
                    print(reply)
                    create_issue(commit_obj , reply , content_hash, content_url)
                    

            else:
                print(content_url, " have problem")
                print(response.text)
                


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        print("webhook received")
        
        print(request.headers)
        ## TODO Make it scalable for many requests
        if request.headers.get("X-Github-Event") == "issue_comment":
            process_issue(request.json)
        elif request.headers.get("X-Github-Event") == "push":
            process_push(request.json)

        data_str = json.dumps(request.json, indent=4)
        filename = 'github_payload.txt'

        with open(filename, 'w') as file:
            file.write(data_str)

        print("data written to file")
        return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
