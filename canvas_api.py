import requests
import os
import boto3

# Set up API credentials
os.environ["OPENAI_API_KEY"] = input("Enter your Canvas API key: ")

BASE_URL = "https://canvas.instructure.com/api/v1"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

ENROLLED_COURSES = {"Geology", 
                    "Fundamentals of Semiconductor Devices", 
                    "Elementary French I Online", 
                    "ECE Design Experience - S25"
                    }
# made canvas access token
# make S3 bucket
# aws configure
S3_BUCKET_NAME = "canvas-files-autodoc"
AWS_REGION = "us-east-2"
s3 = boto3.client("s3")
existing_buckets = [bucket['Name'] for bucket in s3.list_buckets()['Buckets']]
if S3_BUCKET_NAME in existing_buckets:
    print(f"✅ Bucket '{S3_BUCKET_NAME}' already exists. Skipping creation.")
else:
    # Create bucket if it doesn’t exist
    s3.create_bucket(
        Bucket=S3_BUCKET_NAME,
        CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
    )
    print(f"🚀 Created new bucket: {S3_BUCKET_NAME}")

# desired_courses = {'18500', }

# Function to fetch all courses with pagination
def get_all_courses():
    url = f"{BASE_URL}/courses"
    courses = []
    
    while url:
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            courses.extend(data)

            # Check if there's another page
            if "next" in response.links:
                url = response.links["next"]["url"]
            else:
                url = None
        else:
            print("Error:", response.json())
            break

    return courses

def get_course_files(course_id):
    url = f"{BASE_URL}/courses/{course_id}/files"
    files = []

    while url:
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            files.extend(data)

            # Check if there's another page
            if "next" in response.links:
                url = response.links["next"]["url"]
            else:
                url = None
        else:
            print("Error:", response.json())
            break

    return files

def get_course_modules(course_id):
    url = f"{BASE_URL}/courses/{course_id}/modules"
    modules = []

    while url:
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            modules.extend(data)

            # Check if there's another page
            if "next" in response.links:
                url = response.links["next"]["url"]
            else:
                url = None
        else:
            print("Error:", response.json())
            break

    return modules

def get_module_items(module_items_url):
    modules_items = []

    while module_items_url:
        response = requests.get(module_items_url, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            modules_items.extend(data)

            # Check if there's another page
            if "next" in response.links:
                module_items_url = response.links["next"]["url"]
            else:
                module_items_url = None
        else:
            print("Error:", response.json())
            break

    return modules_items
        
def upload_s3(course_name, module_name, file_name, file_url):
    s3_key = f"{course_name}/{module_name}/{file_name}"
    print(f"📥 Streaming & uploading: {file_name} → s3://{S3_BUCKET_NAME}/{s3_key}")
    # 🔹 Stream the file from Canvas
    response = requests.get(file_url, headers=HEADERS)

    if response.status_code == 200:
        file_metadata = response.json()
        print("File Metadata:", file_metadata)
    else:
        print("Failed to fetch file metadata:", response.status_code)
        
    download_url = file_metadata.get("url")
    if not download_url:
        print("Download URL not found in metadata.")
    else:
        print("Download URL:", download_url)
        
        
    response = requests.get(download_url, headers=HEADERS, stream=True)

    if response.status_code == 200:
        file_content = response.content
        file_size = len(file_content)
        print(f"Downloaded file size: {file_size} bytes")
    else:
        print("Failed to download file:", response.status_code)
    

    print(f"File size: {len(response.content)} bytes")
    # 🔹 Upload to S3 directly from response content
    s3.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=s3_key,
        Body=file_content
    )


# Fetch and print all courses
courses = get_all_courses()
for course in courses:
    if "name" in course and course["name"] in ENROLLED_COURSES:
        try:
            course_name = course["name"]
            modules = get_course_modules(course["id"])
            for module in modules:
                module_name = module["name"]
                module_items_url = module['items_url']
                module_items = get_module_items(module_items_url)
                for module_item in module_items:
                    if module_item["type"] == "File":
                        file_name = module_item["title"]
                        
                        file_url = module_item["url"]
                        
                        # print(file_name, file_url)
                        upload_s3(course_name, module_name, file_name, file_url)
        except:
            continue



