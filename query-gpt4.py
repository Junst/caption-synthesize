import base64
import requests
import os
# OpenAI API Key
API_KEY = "" #os.environ.get("OPENAI_API_KEY", None)
assert API_KEY is not None, "Please set your OPENAI_API_KEY environment variable"

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')


TAGS_TEMPLATE = r"""
Analyze the image in a comprehensive and detailed manner.
Answer with JSON structure.
The response should have RESPONSE, RATING, and optional ADDITIONAL_TAGS key.
If the image is Photo or Ungiven, you should answer with "PHOTO" then end the response.

If tags are given, You must use the given tags, and reorder them to explain the image.
You must not explain the unrecognized subject or features.

You must include the given tags in RESPONSE value.
ADDITIONAL_TAGS should be the tags that are not given, but you think it is necessary to explain the image.
If Copyright or Character is not given, you should skip the explanation.
You SHOULD try to use and reorder the given tags to construct sentences, instead of fully new sentences summary.

Inside RESPONSE, you should only include information about image itself. 
Mark if image may contain the sensitive content or exposure / sexually problematic content as RATING:<SAFE/QUESTIONABLE/EXPLICIT>
You can REJECT the response for explicit content. In that case, End the response with RATING:EXPLICIT. 

RATING related sentences should NOT be included in RESPONSE value.

Respond with JSON format.

TAG:
{TAGS}
RESPONSE JSON FORMAT:
{
"RESPONSE" : "<STR>",
"RATING" : "<STR>",
"ADDITIONAL_TAGS" : "<STR>"
}
"""
def query_image_with_tags(image_path, tags_txt):
    """
    Query the GPT-4 model with the given image and tags.
    """
    base64_image = encode_image(image_path)
    # load tags
    with open(tags_txt, 'r') as f:
        tags = f.read()
    base64_image = encode_image(image_path)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    tag_txt_formatted = TAGS_TEMPLATE.replace('{TAGS}', tags)
    assert "general" in tag_txt_formatted, "Tags must contain general tag"
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": tag_txt_formatted
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    return response.json()



def query_image_with_text(image_path, text):
    """
    Query the GPT-4 model with the given image and text.
    (Text is not used here, fix it later)
    """
    # Getting the base64 string
    base64_image = encode_image(image_path)

    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": """
Analyze the image in a comprehensive and detailed manner.
Answer with JSON structure.
The response should have RESPONSE, RATING, and optional ADDITIONAL_TAGS key.
If the image is Photo or Ungiven, you should answer with "PHOTO" then end the response.
If tags are given, You must use the given tags, and reorder them to explain the image.
You must not explain the unrecognized subject or features.
Closer tags should be located closely. 
Inside RESPONSE, you should only include information about image itself. DO NOT include the given tag information itself in RESPONSE.
Detect if the image has abnormal anatomy or distortions and mark as "mutated hand" / ETC.
Mark if image may contain the sensitive content or exposure / sexually problematic content as RATING:<SAFE/QUESTIONABLE/EXPLICIT.
You can reject the response for explicit content. In that case, End the response with RATING:EXPLICIT. 

RATING related sentences should NOT be included in RESPONSE value.
Start the response with RESPONSE: "<Put your response here>"
            """
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    return response.json()

import glob
import tqdm
import json

DEBUG_LIMIT = 1000000
def query_gpt4(path):
    images = glob.glob(os.path.join(path, '*.png'))
    _i = 0
    for image in tqdm.tqdm(images):
        if _i > DEBUG_LIMIT:
            break
        # if json already exists, skip
        if os.path.exists(image.replace('.png', '.json')):
            continue
        data = query_image_with_text(image, "")
        with open(image.replace('.png', '.json'), 'w') as f:
            json.dump(data, f, indent=4)
        _i += 1

def query_gpt4_with_tags(path, file_ext='.png'):
    images = glob.glob(os.path.join(path, f'*{file_ext}'))
    _i = 0
    for image in tqdm.tqdm(images):
        if _i > DEBUG_LIMIT:
            break
        # if json already exists, skip
        if os.path.exists(image.replace(file_ext, '_gpt4.json')):
            print("Already exists")
            continue
        if not os.path.exists(image.replace(file_ext, '.txt')):
            print("No tags")
            continue
        tags_txt = image.replace(file_ext, '.txt')
        data = query_image_with_tags(image, tags_txt)
        with open(image.replace(file_ext, '_gpt4.json'), 'w') as f:
            json.dump(data, f, indent=4)
        _i += 1

if __name__ == '__main__':
    query_gpt4_with_tags(r"D:\aibooru_subset_g_100img", '.jpg')
