"""
Jarvis - a simple voice assistant for Windows.

How to use:
  * Press ENTER and talk, or type your message and press ENTER.
  * Type "exit" (or say "goodbye") to quit.

Jarvis prints every step ("Listening...", "You said: ...") so you can
always see what is happening. If the microphone does not work, you can
still type to him.
"""

import datetime
import os
import subprocess
import sys
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(HERE, "api_key.txt")

# Easy questions go to the cheap, fast model; harder ones to the smart one.
FAST_MODEL = "claude-haiku-4-5"
SMART_MODEL = "claude-opus-5"
HARD_WORDS = (
    "explain", "why", "how does", "how do", "how can", "write", "code",
    "program", "plan", "compare", "difference", "analy", "story", "essay",
    "summar", "step by step", "calculate", "solve", "think hard", "advice",
)
SYSTEM_PROMPT = (
    "You are Jarvis, a friendly voice assistant. Your answers are read out "
    "loud, so keep them short (1-3 sentences), conversational, and never use "
    "markdown, bullet points, code blocks or emojis."
)


# ---------------------------------------------------------------- speaking

def speak(text):
    print(f"Jarvis: {text}")
    if sys.platform != "win32":
        return
    try:
        # Fast path: Windows speech engine via pywin32 (if installed).
        import win32com.client

        win32com.client.Dispatch("SAPI.SpVoice").Speak(text)
        return
    except Exception:
        pass
    try:
        # Fallback: Windows' built-in speech through PowerShell. Always available.
        subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                "Add-Type -AssemblyName System.Speech; "
                "(New-Object System.Speech.Synthesis.SpeechSynthesizer)"
                ".Speak([Console]::In.ReadToEnd())",
            ],
            input=text, text=True, encoding="utf-8", check=False,
        )
    except Exception as e:
        print(f"  (Could not speak out loud: {e})")


# --------------------------------------------------------------- listening

class Ears:
    """Microphone input. Falls back to typing-only if the mic can't be used."""

    def __init__(self):
        self.ok = False
        try:
            import speech_recognition as sr

            self.sr = sr
            self.recognizer = sr.Recognizer()
            self.mic = sr.Microphone()
            print("Checking your microphone (stay quiet for 1 second)...")
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.ok = True
            print("Microphone is working.")
        except Exception as e:
            print("\n!! The microphone could not be started, so you can only TYPE to Jarvis.")
            print(f"!! Reason: {e}")
            print("!! Check that a microphone is plugged in and that Windows allows apps")
            print("!! to use it (Settings > Privacy & security > Microphone).\n")

    def listen(self):
        sr = self.sr
        try:
            with self.mic as source:
                print("Listening... speak now.")
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=15)
        except sr.WaitTimeoutError:
            speak("I didn't hear anything.")
            return None
        print("Got it, understanding what you said...")
        try:
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that. Please try again.")
        except sr.RequestError as e:
            print(f"  (Speech service error: {e})")
            speak("I can't reach the speech service. Please check your internet connection.")
        return None


# ------------------------------------------------------------------- brain

def load_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key and os.path.exists(KEY_FILE):
        with open(KEY_FILE, encoding="utf-8") as f:
            key = f.read().strip()
    return key or None


class Brain:
    def __init__(self):
        self.client = None
        self.history = []
        key = load_api_key()
        if not key:
            print("No API key found: Jarvis can only do the built-in commands")
            print("(time, date, open youtube, open google, search ...).")
            print(f"To let him answer anything, put your Claude API key in: {KEY_FILE}\n")
            return
        try:
            import anthropic

            self.anthropic = anthropic
            self.client = anthropic.Anthropic(api_key=key)
        except ImportError:
            print("The 'anthropic' package is missing. Run START_JARVIS.bat again.\n")

    def ask(self, text):
        if not self.client:
            return ("I can only do simple commands until you add an API key. "
                    "Try asking me the time, or say open YouTube.")
        anthropic = self.anthropic
        self.history.append({"role": "user", "content": text})
        model = pick_model(text)
        print("  (quick mode)" if model == FAST_MODEL else "  (smart mode)")
        try:
            if model == FAST_MODEL:
                response = self.client.messages.create(
                    model=FAST_MODEL,
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    messages=self.history,
                )
            else:
                response = self.client.beta.messages.create(
                    model=SMART_MODEL,
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    messages=self.history,
                    output_config={"effort": "low"},  # quick answers for voice
                    # If Claude declines a request, the API retries it on another model.
                    betas=["server-side-fallback-2026-07-01"],
                    fallbacks="default",
                )
        except anthropic.AuthenticationError:
            self.history.pop()
            return "My API key was rejected. Please check the key in api key dot t x t."
        except anthropic.RateLimitError:
            self.history.pop()
            return "I'm being rate limited, or your API account is out of credit. Try again soon."
        except anthropic.APIStatusError as e:
            self.history.pop()
            print(f"  (API error {e.status_code}: {e.message})")
            return "Something went wrong talking to my brain. The error is shown on screen."
        except anthropic.APIConnectionError:
            self.history.pop()
            return "I can't connect to the internet right now."

        if response.stop_reason == "refusal":
            self.history.pop()
            return "Sorry, I can't help with that."

        answer = " ".join(b.text for b in response.content if b.type == "text").strip()
        answer = answer or "I'm not sure what to say to that."

        # Only the spoken text is kept, since the two models can't share each
        # other's thinking blocks.
        self.history.append({"role": "assistant", "content": answer})
        self.history = self.history[-20:]
        while self.history and self.history[0]["role"] != "user":
            self.history.pop(0)
        return answer


def pick_model(text):
    t = text.lower()
    if len(t.split()) > 25 or any(w in t for w in HARD_WORDS):
        return SMART_MODEL
    return FAST_MODEL


# ---------------------------------------------------------------- commands

def handle_command(text):
    """Built-in commands that work without an API key. Returns a reply or None."""
    t = text.lower().strip()
    now = datetime.datetime.now()
    if "time" in t and ("what" in t or t == "time"):
        return f"It's {now.strftime('%I:%M %p').lstrip('0')}."
    if "date" in t or "what day" in t:
        return f"Today is {now.strftime('%A, %B %d, %Y')}."
    if t.startswith("open youtube"):
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."
    if t.startswith("open google"):
        webbrowser.open("https://www.google.com")
        return "Opening Google."
    if t.startswith("search "):
        query = text.strip()[7:]
        webbrowser.open("https://www.google.com/search?q=" + query.replace(" ", "+"))
        return f"Searching Google for {query}."
    return None


def wants_to_quit(text):
    t = text.lower().strip(" .!")
    return t in {"exit", "quit", "stop", "goodbye", "bye", "goodbye jarvis", "bye jarvis"}


# -------------------------------------------------------------------- main

def main():
    print("=" * 60)
    print("  JARVIS")
    print("=" * 60)
    ears = Ears()
    brain = Brain()
    speak("Jarvis online. How can I help?")

    while True:
        prompt = ("\n[Press ENTER and talk]  or  [type a message + ENTER]  (type exit to quit)\n> "
                  if ears.ok else "\n[Type a message + ENTER]  (type exit to quit)\n> ")
        try:
            typed = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            break

        if typed:
            text = typed
        elif ears.ok:
            text = ears.listen()
            if not text:
                continue
            print(f"You said: {text}")
        else:
            continue

        if wants_to_quit(text):
            break

        print("Thinking...")
        reply = handle_command(text) or brain.ask(text)
        speak(reply)

    speak("Goodbye.")


if __name__ == "__main__":
    main()
