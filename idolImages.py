import os
import random
from dotenv import load_dotenv

load_dotenv()

def get_available_idols():
    base_folder = os.getenv("IDOL_IMAGE_FOLDER", "images")
    if not os.path.exists(base_folder):
        return[]
    
    return [
        folder.replace("_", " ").title()
        for folder in os.listdir(base_folder)
        if os.path.isdir(os.path.join(base_folder, folder))
    ]

async def get_idol_image(idol_name: str):
    base_folder = os.getenv("IDOL_IMAGE_FOLDER")
    folder_name = idol_name.lower().replace(" ", "_")
    target_path = os.path.join(base_folder, folder_name)

    if not os.path.exists(base_folder):
        return None

    image_files = []
    for root, dirs, files in os.walk(target_path):
        for file in files:
            if file.endswith(('.jpg', '.jpeg', '.png')):
                image_files.append(os.path.join(root, file))
    
    return random.choice(image_files) if image_files else None