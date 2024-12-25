import json
import random
import re
import os
from groq import Groq

client = Groq(api_key="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")

input_file_paths = ["ProcessedAppData/org_healthcare_appdata.json"]  # List of input file paths
output_folder_path = "LLM_Processed_Files"  # Folder to store output files
MAX_RETRIES = 3
Counter = 0

# Variables to track the number of stories generated and successfully parsed
total_stories_generated = 0
total_stories_parsed = 0

if not os.path.exists(output_folder_path):
    os.makedirs(output_folder_path)

def parse_user_story_output(user_story, path_metadata, available_apps):
    global total_stories_parsed  # Track parsed stories
    try:
        json_block_pattern = r"```json\s*(.*?)\s*```"
        json_match = re.search(json_block_pattern, user_story, re.DOTALL)

        if json_match:
            json_data = json_match.group(1).strip()

            try:
                parsed_json = json.loads(json_data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Malformed JSON in ```json...``` block: {e}")

        elif "<jsonstart>" in user_story and "<jsonend>" in user_story:
            json_data_pattern = r"<jsonstart>(.*?)<jsonend>"
            json_match = re.search(json_data_pattern, user_story, re.DOTALL)

            if json_match:
                json_data = json_match.group(1).strip()

                try:
                    parsed_json = json.loads(json_data)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Malformed JSON between <jsonstart> and <jsonend>: {e}")

        else:
            try:
                parsed_json = json.loads(user_story.strip())
            except json.JSONDecodeError as e:
                raise ValueError(f"Malformed JSON in raw user story: {e}")

        if "User Stories" in parsed_json:
            for user_story in parsed_json["User Stories"]:
                user_story["App Names"] = available_apps

            total_stories_parsed += len(parsed_json["User Stories"])  # Increment parsed stories

        return {
            "metadata": path_metadata,
            "data": parsed_json
        }

    except Exception as e:
        print(f"Error parsing user story output: {e}")
        return None

def generate_combinations(features, max_combinations=10):
    variations = []
    while len(variations) < max_combinations:
        num_features = min(random.randint(1, 3), len(features))
        selected_features = random.sample(features, num_features)

        feature_details = {
            "Features": [feature["Feature"] for feature in selected_features],
            "Available Apps": {},
            "Acceptance Criteria": set(),
            "Common Bugs": set(),
        }

        for feature in selected_features:
            for region, app_list in feature.get("apps", {}).items():
                feature_details["Available Apps"].setdefault(region, set()).update(app_list)

            feature_details["Acceptance Criteria"].update(
                feature.get("acceptance_criteria", {}).get("mobile", [])
            )
            feature_details["Common Bugs"].update(
                feature.get("common_bugs", {}).get("mobile", [])
            )

        feature_details["Available Apps"] = {k: list(v) for k, v in feature_details["Available Apps"].items()}
        feature_details["Acceptance Criteria"] = list(feature_details["Acceptance Criteria"])
        feature_details["Common Bugs"] = list(feature_details["Common Bugs"])

        variations.append(feature_details)

    return variations

def traverse_hierarchy(data, path=[]):
    solutions = []
    for key, value in data.items():
        current_path = path + [key]
        if isinstance(value, dict):
            solutions += traverse_hierarchy(value, current_path)
        elif isinstance(value, list):
            solutions.append({
                "Path": current_path[:-1],
                "Requirement Type": current_path[-1],
                "Features": value
            })
    return solutions

def generate_user_story_for_all_qualities(feature_details, domain, subdomain, platform, software_type,
                                          requirement_type):
    example_json = """
    ```json
        {
            "Feature Name": ["feature1", "feature2"],
            "User Stories": [
                {
                    "Quality": "High",
                    "User Story": "As a user, I want feature1 and feature2 so that I can achieve specific goals related to both features.",
                    "Acceptance Criteria": ["Acceptance criterion 1", "Acceptance criterion 2"],
                    "Common Bugs": ["Bug 1", "Bug 2"]
                },
                {
                    "Quality": "Average",
                    "User Story": "As a user, I want feature1 and feature2 for improved functionality.",
                    "Acceptance Criteria": ["Acceptance criterion 1", "Acceptance criterion 2"],
                    "Common Bugs": ["Bug 1"]
                },
                {
                    "Quality": "Low",
                    "User Story": "As a user, I want feature1.",
                    "Acceptance Criteria": ["Acceptance criterion 1"],
                    "Common Bugs": ["Bug 1"]
                }
            ]
        }
    ```
    """

    prompt = f"""
                                        Context Information 
                                            - Domain: {domain}
                                            - Subdomain: {subdomain}
                                            - Platform Name: {platform}
                                            - Software Type: {software_type}
                                            - Requirement Type: {requirement_type}

                                        Features Overview 
                                            - The following features are included in this variation: {', '.join(feature_details['Features'])}

                                        Acceptance Criteria 
                                            - The features are expected to meet the following acceptance criteria: {', '.join(feature_details['Acceptance Criteria'])}

                                        Common Bugs 
                                            - These are the known issues: {', '.join(feature_details['Common Bugs'])}

                                        Task 
                                        Please generate three versions of the user story based on the above context and features described. The output must **only** be in JSON format. 
                                        All user story must be drafted in a way that they are related to all given parameters. 
                                        NOTE: All user story must be drafted in a way that they are related to features given as parameter {', '.join(feature_details['Features'])}.
                                        NOTE: The user role should shape the user story by highlighting how the feature and user goal specifically impact the app's usage from the perspective of that user role.

                                        1. High Quality User Story: 
                                            - Be rich in details, the feature interactions, and how the features collectively address the user's needs, without unnecessary information.
                                            - Consider the complexity and challenges involved, while ensuring the story is clear and actionable.
                                            - Return the list of acceptance criteria and common bugs associated with this user story, each of them should be one-liner statements. 

                                        2. Average Quality User Story:
                                            - Be moderately detailed, balancing clarity and brevity while addressing the primary goals and expected feature behavior.
                                            - Focus on the key features and expected outcomes without overwhelming the user with excessive detail.
                                            - Return the list of acceptance criteria and common bugs associated with this user story.

                                        3. Low Quality User Story:
                                            - Be minimalistic, focusing only on the essential user goals and leaving some elements missing or not following the format across the story.
                                            - The story should be concise, may be irrelevant and may not be to the point, with less cohesion and fewer details.
                                            - Return the list of acceptance criteria and common bugs associated with this user story, you must always return at least one for each.

                                        User Story Guidelines
                                            - The user stories should follow this format: As a [user role], I want [feature(s)] so that [user goal].
                                            - Do not use region name and available app names in user story. 
                                            - High Quality and Average Quality, must follow this story format.

                                        Output Format
                                        - Strictly Follow the below format for the user story generation process for each and every iteration.
                                        {example_json}

                                        Ensure the output is strictly in JSON format with no explanation or other text.
                            """
    return prompt

for json_file_path in input_file_paths:
    try:
        with open(json_file_path, "r") as file:
            data = json.load(file)

        all_groups = traverse_hierarchy(data)

        file_name = os.path.basename(json_file_path)
        output_file_path = os.path.join(output_folder_path, f"LLM_{file_name}")

        with open(output_file_path, "w") as output_file:
            output_file.write("[\n")

            first_entry = True

            for group in all_groups:
                features = group["Features"]
                requirement_type = group["Requirement Type"]
                path = group["Path"]
                variations = generate_combinations(features, max_combinations=2)

                subdomain, platform, software_type = path
                path_metadata = {
                    "Subdomain": subdomain,
                    "Platform": platform,
                    "Software Type": software_type,
                    "Requirement Type": requirement_type,
                }

                for variation in variations:
                    prompt = generate_user_story_for_all_qualities(
                        variation, "healthcare", subdomain, platform, software_type, requirement_type
                    )

                    retries = 0
                    while retries < MAX_RETRIES:
                        try:
                            completion = client.chat.completions.create(
                                model="llama-3.1-70b-versatile",
                                messages=[{"role": "user", "content": prompt}],
                                temperature=1,
                                max_tokens=512,
                                top_p=1,
                                stream=True,
                            )

                            user_story_raw = "".join(chunk.choices[0].delta.content or "" for chunk in completion)

                            total_stories_generated += 3  # Increment generated stories
                            print(f"Generation Successful for {subdomain} -> {platform} -> {software_type} -> {requirement_type}")

                            parsed_data = parse_user_story_output(
                                user_story_raw, path_metadata, variation["Available Apps"]
                            )

                            if parsed_data:
                                if first_entry:
                                    json.dump(parsed_data, output_file, indent=2)
                                    first_entry = False
                                else:
                                    output_file.write(",\n")
                                    json.dump(parsed_data, output_file, indent=2)

                            break



                        except Exception as e:
                            print(f"Error generating user story (Attempt {retries + 1}/{MAX_RETRIES}): {e}")
                            retries += 1

                            if retries == MAX_RETRIES:
                                print("Max retries reached. Skipping this variation.")
                    print(f"Data successfully written to {output_file_path}")
                    print(f"Total Stories Generated: {total_stories_generated}")
                    print(f"Total Stories Parsed: {total_stories_parsed}")
            output_file.write("\n]")



    except Exception as e:
        print(f"Error processing JSON file {json_file_path}: {e}")
