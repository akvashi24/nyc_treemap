import requests
import sys
import csv
import os


def extract_tree_id(url):
    """Extract the 7-digit tree ID from the URL."""
    parts = url.strip().split("/")
    try:
        tree_id = int(parts[-1])
        if len(str(tree_id)) == 7:
            return tree_id
    except ValueError:
        pass
    return None


def fetch_tree_data(tree_id):
    """Query NYC Tree Map GraphQL API for data about a tree."""
    url = "https://treemap-api1.nycgovparks.org/nmdapi/graphql"
    headers = {"Content-Type": "application/json"}
    payload = {
        "operationName": "tree",
        "variables": {"id": tree_id},
        "query": """
            query tree($id: Int!) {
              tree(id: $id) {
                id
                species {
                  id
                  scientificName
                  commonName
                  color
                  speciesPhotoId
                  mainSpeciesId
                  cultivarName
                  __typename
                }
              }
            }
        """,
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(
            f"Request for tree {tree_id} failed with status code {response.status_code}"
        )
        return None


def download_image(photo_id, download_dir="images"):
    """Download the image from NYC Parks Cloudinary and return local filepath."""
    if not photo_id:
        return ""

    os.makedirs(download_dir, exist_ok=True)
    url = f"https://res.cloudinary.com/nycparks/image/upload/c_scale,w_auto/c_scale,w_auto/dpr_1.0/f_auto/q_auto:best/d_tree-map:species:defaulttmspecies.jpg/v1/tree-map/species/{photo_id}_tmspecies.png?_a=AJCihWI0"
    filepath = os.path.join(download_dir, f"{photo_id}_tmspecies.png")

    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(filepath, "wb") as out_file:
                for chunk in response.iter_content(chunk_size=8192):
                    out_file.write(chunk)
            return filepath
        else:
            print(
                f"Image download failed for photo ID {photo_id} with status code {response.status_code}"
            )
    except Exception as e:
        print(f"Error downloading image for {photo_id}: {e}")

    return ""


def process_file(input_filename, output_filename):
    with open(input_filename, "r") as file, open(
        output_filename, "w", newline=""
    ) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["commonName", "speciesPhotoId", "imageFilePath"])

        for line in file:
            tree_id = extract_tree_id(line)
            if tree_id:
                data = fetch_tree_data(tree_id)
                if data:
                    species = data.get("data", {}).get("tree", {}).get("species", {})
                    common_name = species.get("commonName", "")
                    photo_id = species.get("speciesPhotoId", "")
                    image_path = download_image(photo_id)
                    writer.writerow([common_name, photo_id, image_path])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <input_filename> <output_filename>")
    else:
        process_file(sys.argv[1], sys.argv[2])
