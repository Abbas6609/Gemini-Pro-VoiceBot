# Necessary Imports
import streamlit as st
import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
import os
from itertools import zip_longest
from concurrent.futures import ThreadPoolExecutor
from htmlTemplates import bot_template, user_template, css
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Google's generative AI API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Load Gemini model
model = genai.GenerativeModel("gemini-pro")

st.set_page_config(page_title="🎙️💬 Tosief's Gemini-Pro Bot 🤖🌟")
st.title("🎙️💬 Tosief's Gemini-Pro Bot 🤖🌟")
st.image(open("Background.jpeg", "rb").read())
st.markdown(css, unsafe_allow_html=True)

# Initialize session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []

executor = ThreadPoolExecutor(max_workers=2)

# Function to use Gemini model for response generation with different configurations for voice and text
def generate_response(user_input, for_voice=False):
    try:
        st.write("Using Gemini model for response.")
        if for_voice:
            # Configuration for voice response: shorter output
            generation_config = genai.types.GenerationConfig(
                candidate_count=1,
                stop_sequences=['x'],
                max_output_tokens=50,
                temperature=1.0)
            response = model.generate_content(user_input, generation_config=generation_config)
        else:
            # Default configuration for text response
            response = model.generate_content(user_input)

        return response.text if response.text else ''
    except Exception as e:
        st.write(f"Error: {e}")
        return "Error generating response"

def build_message_list():
    zipped_messages = []
    for human_msg, ai_msg in zip_longest(st.session_state['past'], st.session_state['generated']):
        if human_msg is not None:
            zipped_messages.append(human_msg)
        if ai_msg is not None:
            zipped_messages.append(ai_msg)
    return zipped_messages

def capture_audio():
    st.info("🎤 Listening... Please speak your question now!")
    r = sr.Recognizer()
    with sr.Microphone(device_index=2) as source:
        audio = r.listen(source, timeout=10)
    st.empty()  # Clears the 'Listening...' message

    try:
        recognized_text = r.recognize_google(audio)
        if recognized_text:
            st.success('Your audio is captured.')  # Display success message
        return recognized_text
    except sr.UnknownValueError:
        st.warning("Could not understand audio, please try again.")
        return ""
    except sr.RequestError:
        st.error("API unavailable. Please check your internet connection and try again.")
        return ""

def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def display_message(message, is_user=False):
    if is_user:
        html_content = user_template.replace('{{MSG}}', message)
    else:
        html_content = bot_template.replace('{{MSG}}', message)

    st.markdown(html_content, unsafe_allow_html=True) # here html

# Display the conversation chain
if st.session_state['generated']:
    for ai_msg, user_msg in zip(st.session_state['generated'], st.session_state['past']):
        if user_msg:
            display_message(user_msg, is_user=True)
        if ai_msg:
            display_message(ai_msg)

# Define the callback function
def clear_text():
    # This will clear the text input
    st.session_state.text_input = ''

# Ensure that the text input uses the session state to retain its value
if 'text_input' not in st.session_state:
    st.session_state['text_input'] = ''

# Add a text input
text_input = st.text_input("Type your question here:", key='text_input', value=st.session_state['text_input'])

# Create a layout for buttons in a single row
# Adjust the column weights as needed to align buttons as desired
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    if st.button("Text Search? ⌨️"):
        if text_input:
            with st.spinner('Processing your query...'):
                st.session_state.past.append(text_input)
                output = generate_response(text_input)
                st.session_state.generated.append(output)
                display_message(output)  # Use custom display function for bot message
                display_message(text_input, is_user=True)  # Use custom display function for user message
        else:
            st.warning("Please enter a question.")

        # Reset the button state
        st.rerun()

with col2:
    if st.button("Ask Question? 🔊"):
        with st.spinner('Listening and processing your query...'):
            user_input = capture_audio()
            if user_input:
                st.session_state.past.append(user_input)
                # Generate the response for voice
                output = generate_response(user_input, for_voice=True)

                # Ensure the text is added to the state and displayed before speaking
                st.session_state.generated.append(output)
                display_message(output)  # Display the bot response
                display_message(user_input, is_user=True)  # Display the user input

                # Call the text-to-speech function
                executor.submit(text_to_speech, output)
            else:
                st.error("No input detected. Please try again.")

        # Reset the button state
        st.rerun()

with col3:
    if st.button("Clear 🗑️", on_click=clear_text):
        # The callback function will be triggered when the button is pressed
        pass  # No need to call st.experimental_rerun()