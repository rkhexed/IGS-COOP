import json
import hashlib
import os


def load_domain(file_path):
    with open(file_path, 'r') as f:
        domain_data = json.load(f)
    return domain_data.get("Domain", "Unknown Domain")


def load_json_file(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)


def generate_id(user_story):
    story_content = json.dumps({
        "User Story": user_story.get("User Story", ""),
        "Acceptance Criteria": user_story.get("Acceptance Criteria", []),
        "Common Bugs": user_story.get("Common Bugs", [])
    }, sort_keys=True)
    return hashlib.sha256(story_content.encode()).hexdigest()


def merge_hierarchical_data(existing_data, new_data):
    """Merge new_data into existing_data, maintaining hierarchy and avoiding duplicates."""
    for new_subdomain in new_data["Subdomains"]:
        existing_subdomain = next(
            (sd for sd in existing_data["Subdomains"] if sd["Subdomain Name"] == new_subdomain["Subdomain Name"]), None)

        if not existing_subdomain:
            existing_data["Subdomains"].append(new_subdomain)
        else:
            for new_region in new_subdomain["Regions"]:
                existing_region = next(
                    (r for r in existing_subdomain["Regions"] if r["Region Name"] == new_region["Region Name"]), None)

                if not existing_region:
                    existing_subdomain["Regions"].append(new_region)
                else:
                    for new_platform in new_region["Platforms"]:
                        existing_platform = next((p for p in existing_region["Platforms"] if
                                                  p["Platform Name"] == new_platform["Platform Name"]), None)

                        if not existing_platform:
                            existing_region["Platforms"].append(new_platform)
                        else:
                            for new_software in new_platform["Software Types"]:
                                existing_software = next(
                                    (st for st in existing_platform["Software Types"] if
                                     st["Software Type Name"] == new_software["Software Type Name"]),
                                    None
                                )

                                if not existing_software:
                                    existing_platform["Software Types"].append(new_software)
                                else:
                                    for req_type in ["Functional", "Non-Functional"]:
                                        existing_requirements = existing_software["Requirements"].get(req_type, [])
                                        new_requirements = new_software["Requirements"].get(req_type, [])

                                        for new_feature in new_requirements:
                                            existing_feature = next(
                                                (f for f in existing_requirements if
                                                 f["Feature Name"] == new_feature["Feature Name"]),
                                                None
                                            )

                                            if not existing_feature:
                                                existing_requirements.append(new_feature)
                                            else:
                                                # Merge user stories
                                                existing_feature["User Stories"].extend(
                                                    us for us in new_feature["User Stories"] if
                                                    us["_id"] not in {e["_id"] for e in
                                                                      existing_feature["User Stories"]}
                                                )
    return existing_data


def process_data(input_data, domain_name):
    output_data = {
        "Domain": domain_name,
        "Subdomains": []
    }

    for entry in input_data:
        subdomain_name = entry["metadata"].get("Subdomain", "Unknown Subdomain")
        platform_name = entry["metadata"].get("Platform", "Unknown Platform")
        software_type_name = entry["metadata"].get("Software Type", "Unknown Software Type")
        requirement_type = entry["metadata"].get("Requirement Type", "Unknown Requirement Type").strip().upper()

        feature_names = entry["data"].get("Feature Name", [])
        if not feature_names:
            continue

        subdomain = next((sd for sd in output_data["Subdomains"] if sd["Subdomain Name"] == subdomain_name), None)
        if not subdomain:
            subdomain = {
                "Subdomain Name": subdomain_name,
                "Regions": []
            }
            output_data["Subdomains"].append(subdomain)

        for user_story in entry["data"].get("User Stories", []):
            apps = user_story.get("App Names", {})
            combined_apps = {region: apps_list for region, apps_list in apps.items()}
            user_story_id = generate_id(user_story)

            for region in apps.keys():
                region_obj = next((r for r in subdomain["Regions"] if r["Region Name"] == region), None)
                if not region_obj:
                    region_obj = {
                        "Region Name": region,
                        "Platforms": []
                    }
                    subdomain["Regions"].append(region_obj)

                platform_obj = next((p for p in region_obj["Platforms"] if p["Platform Name"] == platform_name), None)
                if not platform_obj:
                    platform_obj = {
                        "Platform Name": platform_name,
                        "Software Types": []
                    }
                    region_obj["Platforms"].append(platform_obj)

                software_type_obj = next(
                    (st for st in platform_obj["Software Types"] if st["Software Type Name"] == software_type_name),
                    None)
                if not software_type_obj:
                    software_type_obj = {
                        "Software Type Name": software_type_name,
                        "Requirements": {
                            "Functional": [],
                            "Non-Functional": []
                        }
                    }
                    platform_obj["Software Types"].append(software_type_obj)

                requirement_list = software_type_obj["Requirements"].get(
                    "Functional" if requirement_type == "FR" else "Non-Functional", []
                )

                feature_obj = next((f for f in requirement_list if f["Feature Name"] == feature_names), None)
                if not feature_obj:
                    feature_obj = {
                        "Feature Name": feature_names,
                        "User Stories": []
                    }
                    requirement_list.append(feature_obj)

                feature_obj["User Stories"].append({
                    "_id": user_story_id,
                    "Quality": user_story.get("Quality", "Unknown Quality"),
                    "User Story": user_story.get("User Story", "Unknown User Story"),
                    "Acceptance Criteria": user_story.get("Acceptance Criteria", []),
                    "Common Bugs": user_story.get("Common Bugs", []),
                    "apps": combined_apps
                })

    return output_data


def save_json_file(data, output_path):
    if os.path.exists(output_path):
        try:
            # Attempt to load existing data
            with open(output_path, 'r') as f:
                content = f.read().strip()
                existing_data = json.loads(content) if content else {"Domain": data["Domain"], "Subdomains": []}
        except json.JSONDecodeError:
            print(f"Warning: File '{output_path}' is empty or corrupt. Initializing as new.")
            existing_data = {"Domain": data["Domain"], "Subdomains": []}

        # Merge with new data
        data = merge_hierarchical_data(existing_data, data)

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)


def main():
    domain_files = [os.path.join('RawAppData', f) for f in os.listdir('RawAppData') if f.endswith('.json')]
    input_files = [os.path.join('LLM_Processed_Files', f) for f in os.listdir('LLM_Processed_Files') if
                   f.endswith('.json')]

    if len(domain_files) != len(input_files):
        print("Warning: The number of input files does not match the number of domain files.")
        return

    if not os.path.exists('Formatted_Schema_Files'):
        os.makedirs('Formatted_Schema_Files')

    for input_file, domain_file in zip(input_files, domain_files):
        try:
            domain_name = load_domain(domain_file)
            input_data = load_json_file(input_file)
            processed_data = process_data(input_data, domain_name)
            output_file_name = f"Formatted_Schema_Files/Merged_{os.path.basename(input_file)}"
            save_json_file(processed_data, output_file_name)
            print(f"Processed data saved to {output_file_name}")

        except Exception as e:
            print(f"Error processing {input_file}: {e}")


if __name__ == "__main__":
    main()
