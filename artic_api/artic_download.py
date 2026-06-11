import logging
import os
import requests

dir_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(dir_path, 'ids_list.txt')
art_image_path = os.path.join(dir_path, 'art_image.jpg')

BASE_URL = "https://api.artic.edu/api/v1/artworks/"
FIELDS = "?fields=id,title,artist_title,image_id"
MAX_ATTEMPTS = 5  # some artworks have image_id = null; skip them


def _rotate_ids():
    """Pop the first id from ids_list.txt, append it to the end, return it."""
    with open(file_path, 'r') as file:
        lines = file.readlines()
    if not lines:
        return None
    first_line = lines.pop(0).rstrip('\n')
    lines.append(first_line + '\n')
    with open(file_path, 'w') as file:
        file.writelines(lines)
    return first_line


def download_image():
    """Download today's artwork.

    Returns (title, artist) on success, or None on failure.
    Skips artworks without an image_id instead of crashing or silently
    keeping yesterday's jpg.
    """
    for attempt in range(MAX_ATTEMPTS):
        image_id = _rotate_ids()
        if image_id is None:
            logging.error("ids_list.txt is empty")
            return None

        try:
            response = requests.get(f"{BASE_URL}{image_id}{FIELDS}", timeout=30)
            response.raise_for_status()
            artwork = response.json()
        except (requests.RequestException, ValueError) as e:
            logging.error(f"Artwork metadata request failed for id {image_id}: {e}")
            return None  # network problem: don't burn through the whole list

        data = artwork.get("data", {})
        title = data.get("title", "Unknown title")
        artist = data.get("artist_title") or "Unknown artist"
        iiif_image_id = data.get("image_id")
        iiif_url = artwork.get("config", {}).get("iiif_url")

        if not iiif_image_id or not iiif_url:
            logging.warning(f"Artwork {image_id} has no image, trying next id")
            continue

        try:
            img_response = requests.get(
                f"{iiif_url}/{iiif_image_id}/full/843,/0/default.jpg", timeout=60)
            img_response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Image download failed for artwork {image_id}: {e}")
            return None

        # Atomic write so a partial download can never leave a truncated
        # art_image.jpg behind (which used to crash convert_to_bmp).
        tmp_path = art_image_path + ".tmp"
        with open(tmp_path, "wb") as file:
            file.write(img_response.content)
        os.replace(tmp_path, art_image_path)
        logging.info(f"Image downloaded successfully: {title} - {artist}")
        return title, artist

    logging.error(f"No artwork with an image found in {MAX_ATTEMPTS} attempts")
    return None


if __name__ == "__main__":
    print(download_image())
