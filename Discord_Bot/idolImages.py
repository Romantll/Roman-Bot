import json
import os
import random




def load_idol_image_data():
    with open("idol_images.json", "r") as f:
        return json.load(f)
    
def get_available_idols():
    data = load_idol_image_data()
    return [idol.title() for idol in data.keys()]

async def get_idol_image(idol_name):
    data = load_idol_image_data()
    key = idol_name.lower().strip()

    if key not in data:
        return None
    
    return random.choice(data[key])