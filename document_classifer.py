import boto3
import json
import os
from collections import defaultdict
from langchain.chat_models import init_chat_model

os.environ["OPENAI_API_KEY"] = input("Enter your OpenAI API key: ")

class CourseFileClassifier:
    def __init__(self, llm=init_chat_model("gpt-4o-mini", model_provider="openai"), s3_bucket_name="canvas-files-autodoc"):
        self.llm = llm
        self.s3 = boto3.client("s3")
        self.s3_bucket_name = s3_bucket_name

    def list_pdf_files(self):
        response = self.s3.list_objects_v2(Bucket=self.s3_bucket_name)

        if "Contents" not in response:
            print("⚠️ No files found in the bucket.")
            return {}

        pdf_files = [obj["Key"] for obj in response["Contents"]]

        class_files = defaultdict(list)
        for file in pdf_files:
            class_name = file.split("/")[0]
            class_files[class_name].append(file)

        return class_files

    def generate_prompt(self, class_files):
        formatted_class_files = "\n".join(
            f"**{class_name}**:\n" + "\n".join(f"- {file}" for file in files)
            for class_name, files in class_files.items()
        )

        return f"""
        You are categorizing course files into **Syllabus** and **Schedule** categories. 
        Your task is to select **one file per class** that is **most likely** to be:
        
        - **Syllabus**: Covers course policies, grading, objectives, and expectations.
        - **Schedule**: Includes dates, deadlines, and a timeline of topics.
        
        If **no file in the class fits the category**, do not select a random file—just leave it blank.
        
        ### **Files Organized by Class**
        {formatted_class_files}

        ### **Output Format (Valid JSON)**
        {{
            "class_name_1": {{"syllabus": "file_path", "schedule": "file_path"}},
            "class_name_2": {{"syllabus": null, "schedule": "file_path"}},
            "class_name_3": {{"syllabus": "file_path", "schedule": null}}
        }}

        Please only return valid JSON.
        """

    def parse_llm_response(self, response):
        raw_text = response.content.strip()

        if raw_text.startswith("```json"):
            raw_text = raw_text[7:-3].strip()

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            print("❌ Error: Invalid JSON response from LLM. Response content:\n", raw_text)
            return {}

    def classify_files(self):
        class_files = self.list_pdf_files()
        if not class_files:
            return {}

        prompt_text = self.generate_prompt(class_files)
        response = self.llm.invoke(prompt_text)

        return self.parse_llm_response(response)
    
    def get_classified_set(self):
        res = set()
        files = self.classify_files()
        
        for course, file_info in files.items():
            if file_info["syllabus"]:
                res.add(file_info["syllabus"])
            if file_info["schedule"]:
                res.add(file_info["schedule"])
        
        return res

