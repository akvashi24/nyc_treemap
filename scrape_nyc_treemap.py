import requests
import sys
import csv
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def fetch_tree_data(tree_id):
    """Query NYC Tree Map GraphQL API for data about a tree."""
    url = "https://treemap-api1.nycgovparks.org/nmdapi/graphql"
    headers = {"Content-Type": "application/json"}
    payload = {
        "operationName": "treeSpeciesById",
        "variables": {"id": int(tree_id), "lang": None},
        "query": """
            query treeSpeciesById($id: Int!, $lang: String) {
              treeSpeciesById(id: $id, lang: $lang) {
                id
                scientificName
                commonName
                color
                description
                speciesPhotoId
                cultivarName
                __typename
              }
            }
        """,
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        logging.debug(f"Successfully fetched data for tree ID {tree_id}")
        return response.json()
    else:
        logging.error(
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
            logging.debug(f"Image downloaded for photo ID {photo_id}")
            return filepath
        else:
            logging.error(
                f"Image download failed for photo ID {photo_id} with status code {response.status_code}"
            )
    except Exception as exception:
        logging.exception(f"Error downloading image for {photo_id}: {exception}")

    return ""


def format_name(common_name):
    """Format the name of the NYC Parks Tree to use capital case"""
    words_in_name = common_name.split(" ")
    capitals = [word.capitalize() for word in words_in_name]
    return " ".join(capitals)


def process_file(input_filename, output_filename):
    logging.info(f"Processing input file: {input_filename}")
    total_lines = 0
    trees_written = 0
    fetched_but_not_written = 0

    with open(input_filename, "r", newline="") as file, open(
        output_filename, "w", newline=""
    ) as csvfile:
        reader = csv.DictReader(file)
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "commonName",
                "imageFilePath",
                "url",
            ]
        )

        for row in reader:
            total_lines += 1
            species_id = row.get("speciesId")
            if not species_id:
                logging.warning("Missing species_id in row, skipping.")
                continue
            data = fetch_tree_data(species_id)
            if data:
                species = data.get("data", {}).get("treeSpeciesById", {})
                common_name = species.get("commonName", "")
                photo_id = species.get("speciesPhotoId", "")
                formatted_name = format_name(common_name)
                logging.info(f"Parsing data for Species {species_id}: {formatted_name}")
                image_path = download_image(photo_id)
                url = f"https://tree-map.nycgovparks.org/tree-map/species/{species_id}"
                if image_path:
                    writer.writerow([formatted_name, image_path, url])
                    trees_written += 1
                else:
                    fetched_but_not_written += 1
                    logging.warning(f"No image found for Species {species_id}")
            else:
                logging.warning(f"No data returned for Species {species_id}")

    logging.info(f"Finished processing. Output written to: {output_filename}")
    logging.info(f"Lines parsed: {total_lines}")
    logging.info(f"Trees written to CSV: {trees_written}")
    logging.info(f"Trees fetched but not written: {fetched_but_not_written}")


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "./species_ids.csv"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "./tree_data.csv"
    process_file(input_file, output_file)
