import requests

url = "http://localhost:8000/api/v1/runner/scenario_execute_from_template"
payload = {
    "template_name": "GenericConversation",
    "scenario_config": {"": {}},
    "agent_configs": {"": {}}
}
response = requests.post(url, json=payload)
print(response.json())