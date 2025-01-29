import requests

# Example: Indeed API interaction
API_KEY = 'your_indeed_api_key'
URL = 'https://api.indeed.com/v2/candidates'

def fetch_candidates():
    headers = {'Authorization': f'Bearer {API_KEY}'}
    response = requests.get(URL, headers=headers)
    if response.status_code == 200:
        candidates = response.json()
        for candidate in candidates:
            print(f"Name: {candidate['name']}, Skills: {candidate['skills']}")
    else:
        print(f"Failed to fetch candidates: {response.status_code}")

fetch_candidates()
