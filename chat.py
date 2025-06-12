import os
import datetime
import random
import re
import logging
from flask import session
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from sympy import sympify, SympifyError
from flask_cors import CORS
import string
from pathlib import Path
import requests
import openai


# Initialize Flask and logging
app = Flask(__name__)
load_dotenv("C:/Users/HP/OneDrive/Desktop/VAL_BOT_AI/openai.env")
app.secret_key = os.getenv("SECRET_KEY")

logging.basicConfig(level=logging.INFO)
CORS(app)

# Load environment variables
load_dotenv(dotenv_path="C:/Users/HP/OneDrive/Desktop/VAL_BOT_AI/openai.env")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

load_dotenv("C:/Users/HP/OneDrive/Desktop/VAL_BOT_AI/openai.env")
key = os.getenv("GROQCLOUD_API_KEY")

res = requests.get(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {key}"}
)
#print(res.status_code, res.json())


# Helper functions
def get_time():
    return datetime.datetime.now().strftime("%I:%M:%S %p") # to get the time

def get_date():
    return datetime.datetime.now().strftime("%Y-%m-%d") # to get the date

def get_weather(city="Nigeria"): # i put a default city to be nigeria, so it print the weather, temp, wind and speed if a city isn't specified by the user.
    if not WEATHER_API_KEY:
        return "Weather API key not set." # here if there is no api key it should return api key not set.
    try: # we use the try and exception method to catch any error
        import requests
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric" # here import the url of the api weather key, i put the api weather key in an env file to save the key and for security
        response = requests.get(url) # here we get the url of the weather api, and send it to the user.
        data = response.json() # here we load the weather api from the json file.
        if data["cod"] == 200: # here if the weather api was gotten successfully it should print out the weather, temp, wind, , speed, and humidity of the city asked by the user.
            desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            hum = data["main"]["humidity"]
            wind = data["wind"]["speed"]
            return f"The weather in {city} is {desc}, {temp}°C, humidity {hum}%, wind speed {wind} m/s." # return the output
        else:
            return f"Couldn't retrieve weather for {city}." # if the chatbot couldn't get the weather api due to any reason like internet connection or bad network it should return the else statement
    except Exception as e:
        logging.error(f"Weather error: {e}")
        return "Error getting weather." # if there was an error getting the weather it should return this
    
def extract_city(user_input_cleaned): # here we use the function extract_city to get the city the user input from the rest of the text.
    known_cities = ["Lagos", "Abuja", "Kano", "New York", "London", "Tokyo", "Paris", "Nigeria"]
    for city in known_cities:
        if city.lower() in user_input_cleaned.lower():
            return city
    return "Nigeria"  # default # this function does this: for any city in the known_cites and it is in the user_input it should return the city nd get the weather info for it.


def tell_joke():
    return random.choice([
        "Why don't scientists trust atoms? Because they make up everything!😄",
        "What do you call a lazy kangaroo? A pouch potato!😄",
        "Parallel lines have so much in common. It’s a shame they’ll never meet.😄",
        "Why did the scarecrow win an award? Because he was outstanding in his field!😄",
    ]) # this is just a joke function to get any joke at of all of this by using random.choice

def is_safe_expression(expr):
    return re.match(r"^[0-9\s\+\-\*\/\^\.\(\)]+$", expr) is not None # this function is for the maths expression 

def extract_math_expression(text):
    # Extract first valid math-like expression from messy text
    matches = re.findall(r'[\d\.\+\-\*/\(\)\s]+', text) # this is to find all the math-like expression and symbols from the user text.
    if matches:
        for expr in matches:
            expr = expr.strip()
            if is_safe_expression(expr):
                return expr
    return None

def clean_input(text):
    return text.lower().strip() # this is to convert text to lower case and separate them


GROQCLOUD_API_KEY = os.getenv("GROQCLOUD_API_KEY")  # Set in your .env file


def generate_valbot_reply(user_input):
    user_input_cleaned = user_input = user_input.strip().lower()
    print(f"[DEBUG] Received user_input: '{user_input_cleaned}'")
    
    
    
    try:

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQCLOUD_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "user", "content": user_input_cleaned}
            ],
            "max_tokens" : 150,
            "temperature": 0.7
            
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            logging.error(f"Groq API error {response.status_code}: {response.text}")
            return "I'm still learning and didn't quite catch that. Want to try something else? 😊"

    except Exception as e:
        logging.error(f"AI reply generation error: {e}")
        return "Oops! Something went wrong while thinking of a reply. 😢"

def save_chat_history(q, a): # here is to save the chat in a json file
    try:
        with open("chat_history.txt", "a", encoding="utf-8") as f:  # here we use the "a" which is the append method to add any new responses and chat between the user and the chatbot to the json file.
            f.write(f"Q: {q}\nA: {a}\n\n")
    except Exception as e:
        logging.error(f"History save error: {e}") #also use the try-exception method to catch errors.

def format_quick_replies(quick_replies):
    if all(isinstance(reply, dict) and "text" in reply for reply in quick_replies):
        return quick_replies
    return [{"text": r, "value": r} for r in quick_replies] #here we format the quick_replies 


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    print(f"[DEBUG] Raw data received: {data}")
    user_input = data.get("message", "").strip()
    
    if not user_input:
        return jsonify({
            "response": "It seems like you may have accidentally sent an empty message! Would you like to ask me something or start a conversation?",
            "quick_replies": []
        })
    user_input_cleaned = f"{user_input.lower()}"
    
    reply = generate_valbot_reply(user_input_cleaned)
    
    if not reply:
        reply = generate_valbot_reply(user_input_cleaned)
        
        #format sentence on a newline
        sentences = re.split(r'(?<=[.!?]) +', reply.strip())
        reply = '\n'.join(sentences)
        
        return jsonify({
            "response": reply
        })
    # Clean and preprocess input
    user_input_cleaned = clean_input(user_input)
    user_input_cleaned = user_input.lower().translate(str.maketrans("", "", string.punctuation))

    response = None
    quick_replies = []
    user_name = session.get("user_name", None)

    logging.info(f"Session user_name: {user_name}")

    # 1. Check if we're waiting for the user's name
    if session.get("awaiting_name"):
        name_patterns = [r"my name is (\w+)", r"i am (\w+)", r"i'm (\w+)", r"^(\w+)$"]
        banned_words = ["food", "weather", "help", "time", "date", "hello", "no", "nice", "maybe", "ok", "good", "bad", "never mind", "okay", "bye"]
        
        found_name = next((re.search(pat, user_input_cleaned) for pat in name_patterns if re.search(pat, user_input_cleaned)), None)

        if found_name:
            name = found_name.group(1).capitalize()
            if name.lower() not in banned_words:
                session["user_name"] = name
                session["awaiting_name"] = False
                response = f"Nice to meet you, {name}! How can I assist you today?"
                quick_replies = [
                    {"text": "What can you do?🤔", "class": "response-quick-replies"},
                    {"text": "What's the weather in Lagos?🌧️", "class": "response-quick-replies"}
                ]
                save_chat_history(user_input, response)
                return jsonify({"response": response, "quick_replies": quick_replies})
        
        # Invalid or no name provided
        response = "Sorry, I didn't catch your name. Please tell me your first name only 😊"
        return jsonify({"response": response, "quick_replies": []})

    # 2. Predefined queries
    TIME_QUERIES = ["what is the time", "what's the time", "tell me the time", "time", "current time?"]
    DATE_QUERIES = ["what is the date", "what's the date", "tell me the date", "date", "current date?", "today's date"]

    # 3. Conversation logic
    if any(p in user_input_cleaned for p in ["how are you", "how do you do", "how's it going"]):
        response = f"I'm doing great, thanks for asking{', ' + user_name if user_name else ''}! How about you?"
        quick_replies = [
            {"text": "I'm good", "class": "response-quick-replies"},
            {"text": "Tell me a joke😀", "class": "response-quick-replies"}
        ]

    elif "bye" in user_input_cleaned or "goodbye" in user_input_cleaned:
        response = "Bye, have a nice day🤗."

    elif any(greet in user_input_cleaned for greet in ["hi", "hello", "hey"]):
        if user_name:
            response = f"Hello, {user_name}! I'm Valbot. How can I assist you today?"
            quick_replies = [
                {"text": "Tell me a joke😀", "class": "response-quick-replies"},
                {"text": "What is the time?🕒", "class": "response-quick-replies"}
            ]
        else:
            session["awaiting_name"] = True
            response = "Hello! I'm Valbot. What is your name?🤗"

    elif any(q in user_input_cleaned for q in TIME_QUERIES):
        response = f"The current time is {get_time()}"
        quick_replies = [
            {"text": "What is the date?", "class": "response-quick-replies"},
            {"text": "What is 5 * 5", "class": "response-quick-replies"}
        ]

    elif user_input_cleaned in DATE_QUERIES:
        response = f"Today's date is {get_date()}"
        quick_replies = [
            {"text": "What is the time?🕒", "class": "response-quick-replies"},
            {"text": "What's the weather?🌧️", "class": "response-quick-replies"}
        ]

    elif "what can you do" in user_input_cleaned:
        response = f"I can do a lot to help you{', ' + user_name if user_name else ''}! I can tell you the time/date, give weather updates🌧️, share jokes😄, do math🧠, and chat with you💻."

    elif "weather" in user_input_cleaned:
        match = re.search(r"(?:weather\s*(?:in|at)?\s*)([a-zA-Z\s]+)?", user_input_cleaned)
        city = "Nigeria"  # Default
        if match and match.group(1):
            temp_city = match.group(1).strip().lower()
            if temp_city not in ["", "please", "now", "today"]:
                city = temp_city
        response = get_weather(city.title())
        quick_replies = [
            {"text": "What is the time?⏳", "class": "response-quick-replies"},
            {"text": "What is the date?", "class": "response-quick-replies"}
        ]

    elif "who created you" in user_input_cleaned or "who is the creator" in user_input_cleaned:
        response = "I was created by a young brilliant developer named Temiloluwa Valentine.😎"
        quick_replies = [
            {"text": "Tell me a joke😄", "class": "response-quick-replies"},
            {"text": "What is the time?⏰", "class": "response-quick-replies"}
        ]

    elif "translate" in user_input_cleaned and "yoruba" in user_input_cleaned:
        match = re.search(r"translate\s+['\"]?(.+?)['\"]?\s+to\s+yoruba", user_input_cleaned)
        if match:
            word = match.group(1)
            translations = {"joy": "Ayọ̀", "love": "Ìfẹ́", "peace": "Àlàáfíà"}
            response = f'"{word}" in Yoruba is "{translations.get(word.lower(), "unknown")}" 🌍'
        else:
            response = "Please tell me which word to translate. 😊"

    elif "bible verse" in user_input_cleaned:
        response = "“Trust in the LORD with all your heart and lean not on your own understanding.” – Proverbs 3:5 ✝️"

    elif "tell me a joke" in user_input_cleaned or "joke" in user_input_cleaned:
        response = tell_joke()
        quick_replies = [
            {"text": "Another joke!😄", "class": "response-quick-replies"},
            {"text": "What is 3+3?", "class": "response-quick-replies"}
        ]

    # 4. Math expressions
    math_expr = extract_math_expression(user_input)
    if math_expr:
        try:
            result = sympify(math_expr)
            response = f"The result of {math_expr} is {result}."
            quick_replies = [
                {"text": "Tell me a joke😀", "class": "response-quick-replies"},
                {"text": "What's the weather today?🌤️", "class": "response-quick-replies"}
            ]
            save_chat_history(user_input, response)
            return jsonify({"response": response, "quick_replies": quick_replies})
        except SympifyError:
            logging.error(f"Sympy couldn't parse: {math_expr}")
        except Exception as e:
            logging.error(f"Math evaluation error: {e}")

    
        # 5. Fallback to AI model
    if not response:
        response = generate_valbot_reply(user_input)
        save_chat_history(user_input, response)

    return jsonify({"response": response, "quick_replies": format_quick_replies(quick_replies)})

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
    