import requests
import sys
import csv
import os
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

GOOGLE_CUSTOM_SEARCH_KEY = os.getenv("GOOGLE_CUSTOM_SEARCH_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

if not GOOGLE_CUSTOM_SEARCH_KEY or not GOOGLE_CSE_ID:
    raise ValueError(
        "Missing GOOGLE_CUSTOM_SEARCH_KEY or GOOGLE_CSE_ID environment variables"
    )


def google_image_search(query):
    url = "https://www.googleapis.com/customsearch/v1"

    # Parameters for image search
    params = {
        "key": GOOGLE_CUSTOM_SEARCH_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "searchType": "image",  # Important: image search
        "num": 1,  # Only get the top result
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "items" in data and len(data["items"]) > 0:
        top_image_link = data["items"][0].get("link")
        return top_image_link
    else:
        logging.warning("Image link not found")


def fetch_tree_data(tree_id):
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


def make_treemap_image_url(photo_id):
    return (
        f"https://res.cloudinary.com/nycparks/image/upload/c_scale,w_auto/c_scale,w_auto/dpr_1.0/f_auto/q_auto:best/d_tree-map:species:defaulttmspecies.jpg/v1/tree-map/species/{photo_id}_tmspecies.png?_a=AJCihWI0"
        if photo_id
        else ""
    )


def download_image_from_url(url, download_dir="images"):
    if not url:
        return ""

    os.makedirs(download_dir, exist_ok=True)
    file_name = os.path.basename(url.split("?")[0])
    filepath = os.path.join(download_dir, file_name)

    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(filepath, "wb") as out_file:
                for chunk in response.iter_content(chunk_size=8192):
                    out_file.write(chunk)
            logging.debug(f"Image downloaded from URL {url}")
            return filepath
        else:
            logging.error(
                f"Image download failed from URL {url} with status code {response.status_code}"
            )
    except Exception as exception:
        logging.exception(f"Error downloading image from URL {url}: {exception}")

    return ""


def format_name(common_name):
    words_in_name = common_name.split(" ")
    capitals = [word.capitalize() for word in words_in_name]
    return " ".join(capitals)


def generate_image_html(image_paths):
    html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">'
    for path in image_paths:
        if path:
            html += f'<img src="{path}" style="width: 100%; height: auto;">'
    html += "</div>"
    return html


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
                "Species Name",
                "Image HTML",
                "URL",
            ]
        )
        for row in reader:
            logging.info(f"Logging tree #{total_lines}")
            total_lines += 1
            species_id = row.get("speciesId")
            if not species_id:
                logging.warning("Missing species_id in row, skipping.")
                continue

            data = fetch_tree_data(species_id)
            if data:
                species = data.get("data", {}).get("treeSpeciesById", {})
                common_name = species.get("commonName", "")
                formatted_name = format_name(common_name)
                photo_id = species.get("speciesPhotoId")
                treemap_leaf_url = make_treemap_image_url(photo_id)

                google_leaf_url = google_image_search(f"{formatted_name} leaf")
                bark_url = google_image_search(f"{formatted_name} bark")
                whole_tree_url = google_image_search(f"{formatted_name} whole tree")

                treemap_leaf_img_path = download_image_from_url(treemap_leaf_url)
                google_leaf_img_path = download_image_from_url(google_leaf_url)
                bark_img_path = download_image_from_url(bark_url)
                whole_tree_img_path = download_image_from_url(whole_tree_url)

                logging.debug(
                    f"{formatted_name} treemap leaf path: {treemap_leaf_img_path}"
                )
                logging.debug(
                    f"{formatted_name} google leaf path: {google_leaf_img_path}"
                )
                logging.debug(f"{formatted_name} bark path: {bark_img_path}")
                logging.debug(
                    f"{formatted_name} whole tree path: {whole_tree_img_path}"
                )

                html = generate_image_html(
                    [
                        treemap_leaf_img_path,
                        google_leaf_img_path,
                        bark_img_path,
                        whole_tree_img_path,
                    ]
                )

                writer.writerow([formatted_name, html])
                trees_written += 1
            else:
                logging.warning(f"No data returned for Species {species_id}")

    logging.info(f"Finished processing. Output written to: {output_filename}")
    logging.info(f"Lines parsed: {total_lines}")
    logging.info(f"Trees written to CSV: {trees_written}")
    logging.info(f"Trees fetched but not written: {fetched_but_not_written}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process NYC tree images.")
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default="./species_ids.csv",
        help="Input CSV file containing species IDs",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="./tree_data.csv",
        help="Output CSV file for tree data",
    )
    args = parser.parse_args()

    process_file(args.input, args.output)
