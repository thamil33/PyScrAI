import requests

url = "http://localhost:8000/api/v1/runner/5/dispatch_live_event"
payload = {
    "event_type": "user_input",
    "event_data": {
        "prompt": "Hello, this is the user speaking!"
    },
    "target_agent_id": 1  # Replace with the actual agent ID you want to target
}
response = requests.post(url, json=payload)
print(response.json())