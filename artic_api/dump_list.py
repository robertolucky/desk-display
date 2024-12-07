import json

# Load the JSON data from the file
with open('intersection_data.json', 'r') as file:
    data = json.load(file)

# Extract the 'id' values
ids = [item['id'] for item in data['data']]

# Save the 'id' values to a new file
with open('ids_list.txt', 'w') as output_file:
    for index, id_value in enumerate(ids, start=1):
        output_file.write(f"{id_value}\n")

print("IDs have been extracted and saved to ids_list.txt.")