import requests
file_path='ids_list.txt'

def download_image(output_name="art_image"):

    with open(file_path, 'r') as file:
        # Read all lines from the file
        lines = file.readlines()

    # Check if the file is not empty
    if lines:
        # Remove the first line
        first_line = lines.pop(0).rstrip('\n')
        
        # Append the first line to the end of the list
        lines.append(first_line + '\n')
        
        # Open the file in write mode to update the content
        with open(file_path, 'w') as file:
            # Write the modified list back to the file
            file.writelines(lines)


    # Set the base URL for the ARTic IIIF API
    base_url = "https://api.artic.edu/api/v1/artworks/"
    image_id = first_line
    end_url="?fields=id,title,artist_title,image_id"

    # Create the URL to fetch the image
    first_request = f"{base_url}{image_id}{end_url}"

    # Send a GET request to download the image
    response = requests.get(first_request)

    # Check if the request was successful
    if response.status_code == 200:
        # Save the image locally
        artwork_data = response.json()
        if "title" in artwork_data["data"]:
            title = artwork_data["data"]["title"]
            print("Title:", title)

        if "image_id" in artwork_data["data"]:
            image_id_url = artwork_data["data"]["image_id"]
            print("Image ID:", image_id_url)
        if "iiif_url" in artwork_data["config"]:
            iiif_url=artwork_data["config"]["iiif_url"]
            print(iiif_url)
        if "artist_title" in artwork_data["data"]:
            artist_title=artwork_data["data"]["artist_title"]
            print("Artist:", artist_title)

        download_image_url=f"{iiif_url}/{image_id_url}/full/843,/0/default.jpg"
        response2 = requests.get(download_image_url)

        if response2.status_code == 200:
            # Save the image locally
            with open(f"{output_name}.jpg", "wb") as file:
                file.write(response2.content)
            print("Image downloaded successfully.")
        return title, artist_title
    else:
        print("Failed to download image.")
        return "Failed" "Download"
    

if __name__ == "__main__":
    download_image()