import speech_recognition as sr
import webbrowser
import pyttsx3
import time

recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def processCommand(c):
    pass

if __name__ == "__main__":
    speak("Initializing Robin....")
    while True:

        r = sr.Recognizer()

        print("recognizing...")
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = r.listen(source, timeout=2, phrase_time_limit=1)
            word = r.recognize_google(audio)
            if word.lower() == "robin":
                speak("Ya")
# listen for command
                with sr.Microphone() as source:
                    print("robin Active...")
                    audio = r.listen(source)
                    command = r.recognize_google(audio)

                    processCommand()

        except Exception as e:
            print("Error; {0}".format(e))
