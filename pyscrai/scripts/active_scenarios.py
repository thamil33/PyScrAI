import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1/runner"

def get_active_scenarios():
    """Fetches and prints the list of currently active scenarios from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/active_scenarios")
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        active_scenarios = response.json()
        
        if active_scenarios:
            print("Currently Active Scenarios:")
            for scenario in active_scenarios:
                print(f"  ID: {scenario.get('id')}, Name: {scenario.get('name')}, Status: {scenario.get('status')}, Started: {scenario.get('started_at')}")
        else:
            print("No scenarios are currently active in the ScenarioRunner.")
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching active scenarios: {e}")
    except json.JSONDecodeError:
        print("Error: Could not decode JSON response from the server.")

if __name__ == "__main__":
    get_active_scenarios()
