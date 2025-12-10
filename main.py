import speech_recognition as sr
import webbrowser
import time
import os
import tempfile
import datetime
import urllib.parse
from dotenv import load_dotenv
load_dotenv()

from gtts import gTTS
from playsound import playsound
from groq import Groq
import pyttsx3

# ------------- CONFIG -------------
# Put your actual Groq API key here

client = Groq(api_key=os.getenv("GROQ_API_KEY"))  # <-- replace this

recognizer = sr.Recognizer()


# ------------- TTS (gTTS primary, pyttsx3 fallback) -------------
def speak(text: str):
    text = str(text)
    print(f"Robin says: {text}")

    # Jarvis-style tone
    jarvis_text = text

    try:
        # Natural online voice with gTTS
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts = gTTS(text=jarvis_text, lang="en")
            tts.save(fp.name)
            path = fp.name

        playsound(path)
        os.remove(path)

    except Exception:
        # Offline fallback
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 170)
            engine.setProperty("volume", 1.0)
            voices = engine.getProperty("voices")
            if voices:
                engine.setProperty("voice", voices[0].id)
            engine.say(jarvis_text)
            engine.runAndWait()
        except Exception as e:
            print("TTS error:", e)


# ------------- Groq: General Chat -------------
def ask_groq_chat(message: str) -> str:
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Robin, a JARVIS-like assistant. "
                        "Be concise, helpful, and slightly formal. "
                        "You can answer in English or simple Hinglish if the user does."
                    ),
                },
                {"role": "user", "content": message},
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"AI error: {e}"


# ------------- Groq: Intent Classification -------------
def classify_command(command: str):
    """
    Returns (intent, extra)
    """
    prompt = f"""
You are an intent classifier for a JARVIS-like desktop assistant named Robin.

User said (Hinglish allowed): "{command}"

You must reply ONLY in this format:
intent|extra

Allowed intents:
open_google, open_youtube, open_whatsapp,
google_search, youtube_search, wikipedia_search,
tell_time, tell_date,
shutdown, restart, lock,
open_spotify, open_vs_code, open_camera, open_explorer, open_notepad,
send_whatsapp,
chat, none

Rules:
- If user says things like "kaisi ho", "kaise ho", "aur batao", "who are you", etc,
  use: chat|<english translation>.
- If user mentions WhatsApp actions (e.g. "send whatsapp", "whatsapp message", "whatsapp pe message bhejo"),
  use: send_whatsapp|<message or target info if any>.
- If user says "open WhatsApp", "whatsapp kholo", "open whatsapp on pc",
  use: open_whatsapp|
- If user clearly wants to search something on Google, use: google_search|<query>.
- If user clearly wants to search something on YouTube, use: youtube_search|<query>.
- If user mentions "Wikipedia", use: wikipedia_search|<topic>.
- If user asks for time, use: tell_time|
- If user asks for date, use: tell_date|
- If user wants shutdown / restart / lock, use shutdown|, restart|, lock|.
- If it's a general knowledge question or general chat, use: chat|<concise English version>.

Respond with:
intent|extra
and nothing else.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Output ONLY: intent|extra"},
                {"role": "user", "content": prompt},
            ],
        )
        raw = completion.choices[0].message.content.strip()
        if "|" in raw:
            intent, extra = raw.split("|", 1)
        else:
            intent, extra = raw, ""
        return intent.lower().strip(), extra.strip()
    except Exception as e:
        print("Intent classification error:", e)
        return "chat", command


# ------------- WhatsApp Messaging Helper -------------
def send_whatsapp_flow():
    # Ask for phone number
    speak("Please tell me the phone number with country code. For example, nine one and then the number.")
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.6)
            audio = recognizer.listen(source, timeout=12, phrase_time_limit=10)
        number_text = recognizer.recognize_google(audio, language="en-IN")
        print("Heard phone:", number_text)
    except Exception:
        speak("Sorry, I could not hear the number.")
        return

    # Extract digits from spoken number
    digits = "".join(ch for ch in number_text if ch.isdigit())
    if not digits:
        speak("I could not detect a valid phone number.")
        return

    # Ask for message text
    speak("What is the message?")
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.6)
            audio = recognizer.listen(source, timeout=12, phrase_time_limit=12)
        msg = recognizer.recognize_google(audio, language="en-IN")
        print("WhatsApp message:", msg)
    except Exception:
        speak("Sorry, I could not hear the message.")
        return

    # Open WhatsApp send URL (this usually works with WhatsApp Desktop or Web)
    url = "https://api.whatsapp.com/send?phone=" + digits + "&text=" + urllib.parse.quote(msg)
    speak("Opening WhatsApp to send your message, sir.")
    webbrowser.open(url)


# ------------- Command Executor -------------
def process_command(text: str):
    text = text.strip()
    if not text:
        speak("I did not catch any command, sir.")
        return

    print("User command:", text)

    intent, extra = classify_command(text)
    print("Intent:", intent, "| Extra:", extra)
    extra = extra or ""

    # --- Apps & Websites ---
    if intent == "open_google":
        speak("Opening Google, sir.")
        webbrowser.open("https://www.google.com")

    elif intent == "open_youtube":
        speak("Opening YouTube, sir.")
        webbrowser.open("https://www.youtube.com")

    elif intent == "open_whatsapp":
        speak("Opening WhatsApp on your PC, sir.")
        os.system(r'start shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App')

    elif intent == "open_spotify":
        speak("Opening Spotify, sir.")
        os.system("start spotify")

    elif intent == "open_vs_code":
        speak("Opening Visual Studio Code, sir.")
        os.system("code")

    elif intent == "open_camera":
        speak("Opening Camera, sir.")
        os.system("start microsoft.windows.camera:")

    elif intent == "open_explorer":
        speak("Opening File Explorer, sir.")
        os.system("explorer")

    elif intent == "open_notepad":
        speak("Opening Notepad, sir.")
        os.system("notepad")

    # --- Search ---
    elif intent == "google_search":
        speak(f"Searching Google for {extra}, sir.")
        url = "https://www.google.com/search?q=" + urllib.parse.quote(extra)
        webbrowser.open(url)

    elif intent == "youtube_search":
        speak(f"Searching YouTube for {extra}, sir.")
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(extra)
        webbrowser.open(url)

    elif intent == "wikipedia_search":
        speak(f"Opening Wikipedia for {extra}, sir.")
        slug = extra.replace(" ", "_")
        webbrowser.open(f"https://en.wikipedia.org/wiki/{slug}")

    # --- Time & Date ---
    elif intent == "tell_time":
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {now}, sir.")

    elif intent == "tell_date":
        today = datetime.datetime.now().strftime("%d %B %Y")
        speak(f"Today is {today}, sir.")

    # --- System Controls ---
    elif intent == "shutdown":
        speak("Shutting down the system now, sir.")
        os.system("shutdown /s /t 0")

    elif intent == "restart":
        speak("Restarting the system, sir.")
        os.system("shutdown /r /t 0")

    elif intent == "lock":
        speak("Locking the system, sir.")
        os.system("rundll32.exe user32.dll,LockWorkStation")

    # --- WhatsApp Messaging ---
    elif intent == "send_whatsapp":
        send_whatsapp_flow()

    # --- General Chat / Fallback ---
    else:
        # Always use the original user text for chat
        reply = ask_groq_chat(text)
        speak(reply)



# ------------- Main Loop (Wake Word + Commands) -------------
if __name__ == "__main__":
    speak("Initializing Robin. At your service, sir.")

    while True:
        # Wake word phase
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.6)
                print("\nListening for wake word 'Robin'...")
                audio = recognizer.listen(source, timeout=12, phrase_time_limit=4)

            try:
                wake = recognizer.recognize_google(audio, language="en-IN")
            except sr.UnknownValueError:
                print("Wake word not understood.")
                continue
            except sr.RequestError as e:
                print("Speech API error (wake):", e)
                speak("Speech recognition service is unavailable, sir.")
                continue

            print("Heard (wake):", wake)

        except sr.WaitTimeoutError:
            print("Wake word timeout, listening again...")
            continue
        except Exception as e:
            print("Wake-word error:", e)
            speak("I had a listening issue, sir.")
            continue

        # Check wake word
        if "rob" in wake.lower() or "robin" in wake.lower():
            speak("Yes, sir.")

            # Command phase
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.6)
                    print("Robin active. Listening for your command...")
                    audio = recognizer.listen(source, timeout=12, phrase_time_limit=12)

                try:
                    command_text = recognizer.recognize_google(audio, language="en-IN")
                except sr.UnknownValueError:
                    speak("Sorry, I did not understand that, sir.")
                    continue
                except sr.RequestError as e:
                    print("Speech API error (command):", e)
                    speak("Speech recognition is not responding, sir.")
                    continue

                print("Command:", command_text)
                process_command(command_text)

            except sr.WaitTimeoutError:
                speak("You were silent, sir. I will wait again.")
                continue
            except Exception as e:
                print("Command error:", e)
                speak("Something went wrong while processing your command, sir.")
                continue
