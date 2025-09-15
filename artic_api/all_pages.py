import requests
import json
from time import sleep
# Define the API endpoint (using Met Museum API as an example)
api_url = "https://api.artic.edu/api/v1/artworks/search"


def fetch_all_pages(base_url, params):
    all_data = []
    page = 1
    
    while True:
        # Add pagination parameters
        params['page'] = page
        params['limit'] = 100  # Max items per page
        
        response = requests.get(base_url, params=params)
        sleep(1)

        if response.status_code == 200:
            try:
                page_data = response.json()
                all_data.extend(page_data['data'])
                
                total_pages = page_data['pagination']['total_pages']
                print(f"Fetched page {page} of {total_pages}")
                
                if page >= total_pages:
                    break
                    
                page += 1
                
            except requests.exceptions.JSONDecodeError as e:
                print("Failed to decode JSON response:", str(e))
                break
        else:
            print("Error fetching artworks:", response.status_code)
            break

    
    return all_data


# Fetch only landscape paintings (classification_title: painting, q: landscape)
params_landscape_paintings = {
    'q': 'landscape',
    'query': {
        'term': {
            'classification_title': 'painting'
        }
    }
}
print("Fetching only landscape paintings (IDs only)...")
landscape_paintings = fetch_all_pages(api_url, params_landscape_paintings)

# Extract only the IDs
landscape_painting_ids = [artwork['id'] for artwork in landscape_paintings]

# Save IDs to JSON
with open('landscape_painting_ids.json', 'w') as f:
    json.dump({'ids': landscape_painting_ids}, f, indent=4)
print(f"Saved {len(landscape_painting_ids)} landscape painting IDs to landscape_painting_ids.json")
