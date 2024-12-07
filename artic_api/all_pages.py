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

# Fetch all paintings
params_paintings = {
    'query': {  
        'term': {
            'classification_title': "painting"
        }
    }
}
print("Fetching all paintings...")
paintings_data = fetch_all_pages(api_url, params_paintings)

# Fetch all impressionism artworks
params_impressionism = {
    'q': "impressionism"
}
print("\nFetching all impressionism artworks...")
impressionism_data = fetch_all_pages(api_url, params_impressionism)

# Create complete datasets
data1 = {'data': paintings_data}
data2 = {'data': impressionism_data}

# Save complete datasets
with open('artwork_data.json', 'w') as f:
    json.dump(data1, f, indent=4)
print(f"\nSaved {len(paintings_data)} paintings to artwork_data.json")

with open('impressionism_data.json', 'w') as f:
    json.dump(data2, f, indent=4)
print(f"Saved {len(impressionism_data)} impressionism artworks to impressionism_data.json")

paintings_ids = set(artwork['id'] for artwork in data1['data'])
impressionism_ids = set(artwork['id'] for artwork in data2['data'])

# Find intersection
common_ids = paintings_ids.intersection(impressionism_ids)

# Create a list of artworks that appear in both searches
intersection_data = {
    'data': [artwork for artwork in data1['data'] if artwork['id'] in common_ids]
}

# Save intersection data to JSON file
with open('intersection_data.json', 'w') as f:
    json.dump(intersection_data, f, indent=4)
print(f"Found {len(common_ids)} artworks that are both paintings and impressionist")
print(f"Saved intersection data to intersection_data.json")
