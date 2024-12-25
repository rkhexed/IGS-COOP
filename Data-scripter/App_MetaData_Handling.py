import json
import hashlib
from collections import defaultdict
import os

def calculate_file_hash(filename):
    hasher = hashlib.md5()
    with open(filename, "rb") as file:
        hasher.update(file.read())
    return hasher.hexdigest()

def has_file_changed(filename, hash_file_suffix=".hash"):
    processed_folder = "ProcessedAppData"
    hash_file = os.path.join(processed_folder, f"{os.path.basename(filename)}{hash_file_suffix}")
    current_hash = calculate_file_hash(filename)

    if os.path.exists(hash_file):
        with open(hash_file, "r") as file:
            saved_hash = file.read().strip()
            if current_hash == saved_hash:
                return False

    with open(hash_file, "w") as file:
        file.write(current_hash)
    return True

def organize_apps(data):
    organized_data = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))

    for subdomain in data.get("Subdomains", []):
        subdomain_name = subdomain.get("Subdomain Name", "Unknown Subdomain")
        for region in subdomain.get("Regions", []):
            region_name = region.get("Region", "Unknown Region")
            for app in region.get("Apps", []):
                app_name = app["name"]

                functional_requirements = app.get("functional_requirements", {})
                for platform, layers in functional_requirements.items():
                    for layer, features in layers.items():
                        for feature in features:
                            if "FR" not in organized_data[subdomain_name][platform][layer]:
                                organized_data[subdomain_name][platform][layer]["FR"] = []
                            feature_found = False
                            for item in organized_data[subdomain_name][platform][layer]["FR"]:
                                if item["Feature"] == feature:
                                    if region_name not in item["apps"]:
                                        item["apps"][region_name] = []
                                    item["apps"][region_name].append(app_name)
                                    if "acceptance_criteria" in app:
                                        item["acceptance_criteria"] = app["acceptance_criteria"]
                                    if "common_bugs" in app:
                                        item["common_bugs"] = app["common_bugs"]
                                    feature_found = True
                                    break
                            if not feature_found:
                                new_feature = {
                                    "Feature": feature,
                                    "apps": {region_name: [app_name]},
                                }
                                if "acceptance_criteria" in app:
                                    new_feature["acceptance_criteria"] = app["acceptance_criteria"]
                                if "common_bugs" in app:
                                    new_feature["common_bugs"] = app["common_bugs"]
                                organized_data[subdomain_name][platform][layer]["FR"].append(new_feature)

                non_functional_requirements = app.get("non_functional_requirements", {})
                for platform, layers in non_functional_requirements.items():
                    for layer, features in layers.items():
                        for feature in features:
                            if "NFR" not in organized_data[subdomain_name][platform][layer]:
                                organized_data[subdomain_name][platform][layer]["NFR"] = []
                            feature_found = False
                            for item in organized_data[subdomain_name][platform][layer]["NFR"]:
                                if item["Feature"] == feature:
                                    if region_name not in item["apps"]:
                                        item["apps"][region_name] = []
                                    item["apps"][region_name].append(app_name)
                                    if "acceptance_criteria" in app:
                                        item["acceptance_criteria"] = app["acceptance_criteria"]
                                    if "common_bugs" in app:
                                        item["common_bugs"] = app["common_bugs"]
                                    feature_found = True
                                    break
                            if not feature_found:
                                new_feature = {
                                    "Feature": feature,
                                    "apps": {region_name: [app_name]},
                                }
                                if "acceptance_criteria" in app:
                                    new_feature["acceptance_criteria"] = app["acceptance_criteria"]
                                if "common_bugs" in app:
                                    new_feature["common_bugs"] = app["common_bugs"]
                                organized_data[subdomain_name][platform][layer]["NFR"].append(new_feature)

    return json.loads(json.dumps(organized_data))

def save_to_file(data, filename):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Data saved to {filename}")

def load_input_file(filename):
    with open(filename, "r") as file:
        return json.load(file)

if __name__ == "__main__":
    input_files = ["RawAppData/healthcare_appdata.json"]
    output_dir = "ProcessedAppData"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for input_file in input_files:
        output_file = os.path.join(output_dir, f"org_{os.path.basename(input_file)}")

        if not has_file_changed(input_file):
            print(f"No changes detected in {input_file}. Skipping...")
        else:
            print(f"Changes detected in {input_file}. Processing...")
            json_data = load_input_file(input_file)
            organized_data = organize_apps(json_data)
            save_to_file(organized_data, output_file)
