from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import random
import os

app = Flask(__name__)
# Load environment variables from .env file
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")
headers = {"Authorization": f"Bearer {API_KEY}"}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def run_ai_model(model, inputs):
    input_data = {"messages": inputs}
    response = requests.post(f"{API_BASE_URL}{model}", headers=headers, json=input_data)
    response.raise_for_status()  
    return response.json()

def scrape_website(url):
    response = requests.get(url)
    response.raise_for_status()  
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.title.string if soup.title else "No Title Found"
    description = soup.find('meta', attrs={'name': 'description'})
    description = description['content'] if description else "No Description Found"
    return title, description

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    product_title = data.get('product', 'No Title')
    product_description = data.get('description', 'No Description')
    

    if data.get('url'):
        title, description = scrape_website(data['url'])
        product_title = title
        product_description = description

    system_prompt = """You are an expert copywriter specializing in creating compelling, concise, and effective ad copy for various platforms and audiences. Your task is to generate ad copy based on the given parameters. Follow these guidelines:

1. Tone: Adapt your writing style to match the specified tone (professional, casual, humorous, Luxury, Adventurous, Friendly etc.).
2. Audience: Tailor the language and messaging to resonate with the target audience.
3. Platform: Consider the typical constraints and best practices of the specified platform.
4. Length: Strictly adhere to the maximum character count provided.
5. Clarity: Ensure the main message and call-to-action are clear and prominent.
6. Engagement: Use language that grabs attention and encourages user interaction.
7. Uniqueness: Highlight what makes the product or service stand out from competitors.
8. Benefits: Focus on the benefits to the user rather than just listing features.
9. Brand Voice: Maintain a consistent brand voice if any brand information is provided.
10. Compliance: Avoid making unsupported claims or using potentially offensive language.
11. output: output should not contain any other extra information."""

    user_prompt = f"""Create a compelling {data['tone']} ad copy for {product_title} & {product_description}. 
    The target audience is {data['audience']}. 
    The ad will be posted on {data['platform']}. 
    Keep it under {data['max_length']} characters."""

    inputs = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    try:
        output = run_ai_model("@cf/meta/llama-3.1-8b-instruct", inputs)
        ad_copy = output.get('result', {}).get('response', 'No response')
        return jsonify({'ad_copy': ad_copy})
    except KeyError:
        return jsonify({'error': 'Failed to generate ad copy'}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
