import os
import sys
import webbrowser
import time
import re
import pyautogui
import pywhatkit
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from AppOpener import open as open_app, close as close_app

app = FastAPI(title="AURA - Advanced System Control")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

def process_single_command(command: str):
    """
    Process a single atomic command.
    """
    command = command.strip()
    response = ""

    # 1. WhatsApp Specific Integration
    if ("whatsapp" in command and "send" in command) or ("send" in command and "to" in command):
        try:
            name = ""
            message = ""
            
            # Strategy 1: "saying" (Explicit message separator)
            # Example: "send message to yuvraj saying hello"
            if "saying" in command:
                parts = command.split("saying")
                message = parts[1].strip()
                # Name is usually between "to" and "saying"
                pre_saying = parts[0]
                if "to" in pre_saying:
                    name = pre_saying.split("to")[1].strip()
            
            # Strategy 2: "send [message] to [name]"
            # Example: "send hello to yuvraj"
            elif "to" in command:
                parts = command.split("to")
                pre_to = parts[0].strip() # "send hello"
                post_to = parts[1].strip() # "yuvraj on whatsapp"
                
                # Clean up name (remove "on whatsapp" if present)
                name = post_to.replace("on whatsapp", "").strip()
                
                # Clean up message
                # Remove "send" or "send message" from the start
                msg_candidate = pre_to
                for prefix in ["send message", "send"]:
                    if msg_candidate.startswith(prefix):
                        msg_candidate = msg_candidate[len(prefix):].strip()
                        break
                message = msg_candidate
            
            if name:
                open_app("whatsapp")
                # Wait for WhatsApp to open and focus (Increased to 4s for slower PCs)
                time.sleep(4.0) 
                
                # Search for the contact
                pyautogui.hotkey('ctrl', 'f')
                time.sleep(1.0)
                
                # Type name
                pyautogui.write(name)
                time.sleep(2.0) # Wait for search results to appear
                
                # Select the first result explicitly
                pyautogui.press('down') 
                time.sleep(0.5)
                
                pyautogui.press('enter') # Open the chat
                time.sleep(1.0) # Wait for chat window to load
                
                if message:
                    # Type the message like a human
                    pyautogui.write(message, interval=0.05)
                    time.sleep(0.5) 
                    pyautogui.press('enter')
                    response = f"Sent to {name}: {message}"
                else:
                    response = f"Opened chat with {name}"
            else:
                response = "I couldn't hear the name. Please say 'Send message to [Name]'."
                
        except Exception as e:
            response = f"Error interacting with WhatsApp: {str(e)}"

    # 2. Advanced App Interaction (Context Aware)
    elif " in " in command and ("type" in command or "search" in command):
        # Handle "type [text] in [app]" or "search [query] in [app]"
        action = "type" if "type" in command else "search"
        parts = command.split(" in ")
        
        # Attempt to parse: "type hello in notepad" -> app="notepad"
        app_name = parts[-1].strip()
        content = " ".join(parts[:-1]).replace(action, "").strip()
        
        # Special case: "in notepad type hello"
        if command.startswith("in "):
            app_name = parts[0].replace("in ", "").strip()
            content = parts[1].replace(action, "").strip()

        if app_name and content:
            try:
                # Special handling for Google/Web
                if app_name in ["google", "chrome", "browser", "internet"]:
                    if action == "search":
                        pywhatkit.search(content)
                        return f"Searching Google for {content}"
                
                # Desktop Apps
                open_app(app_name, match_closest=True, output=False)
                time.sleep(1.5) # Wait for focus
                
                if action == "search":
                    # Generic App Search (Ctrl+F)
                    pyautogui.hotkey('ctrl', 'f')
                    time.sleep(0.5)
                    pyautogui.write(content)
                    pyautogui.press('enter')
                    return f"Searched for {content} in {app_name}"
                else:
                    # Typing with special formatting
                    if "new line" in content:
                        lines = content.split("new line")
                        for line in lines:
                            pyautogui.write(line.strip())
                            pyautogui.press('enter')
                    else:
                        pyautogui.write(content)
                    return f"Typed in {app_name}: {content}"
            except:
                return f"Could not access {app_name}."

    # 3. Generic Keyboard, Window & Media Control
    elif "scroll" in command:
        if "down" in command:
            pyautogui.scroll(-1000)
            return "Scrolling down."
        elif "up" in command:
            pyautogui.scroll(1000)
            return "Scrolling up."
            
    elif "volume" in command:
        if "up" in command or "increase" in command:
            pyautogui.press("volumeup", presses=5)
            return "Increasing volume."
        elif "down" in command or "decrease" in command:
            pyautogui.press("volumedown", presses=5)
            return "Decreasing volume."
        elif "mute" in command:
            pyautogui.press("volumemute")
            return "Muting audio."
            
    elif "media" in command or "music" in command:
        if "play" in command or "pause" in command or "stop" in command:
            pyautogui.press("playpause")
            return "Toggling media playback."
        elif "next" in command or "skip" in command:
            pyautogui.press("nexttrack")
            return "Skipping track."
        elif "previous" in command or "back" in command:
            pyautogui.press("prevtrack")
            return "Previous track."

    elif "type" in command:
        text = command.replace("type", "").strip()
        if "new line" in text:
            pyautogui.press('enter')
        else:
            pyautogui.write(text)
        return "Typing..."
        
    elif "press" in command or "hit" in command:
        key = command.replace("press", "").replace("hit", "").strip()
        if "enter" in key: pyautogui.press('enter')
        elif "space" in key: pyautogui.press('space')
        elif "backspace" in key or "delete" in key: pyautogui.press('backspace')
        else: pyautogui.press(key)
        return f"Pressed {key}"
        
    elif "save" in command: # Save file
        pyautogui.hotkey('ctrl', 's')
        return "Saved."
    elif "select all" in command:
        pyautogui.hotkey('ctrl', 'a')
        return "Selected all."
    elif "copy" in command:
        pyautogui.hotkey('ctrl', 'c')
        return "Copied."
    elif "paste" in command:
        pyautogui.hotkey('ctrl', 'v')
        return "Pasted."
    elif "minimize" in command:
        pyautogui.hotkey('win', 'down')
        pyautogui.hotkey('win', 'down') # Twice often needed
        return "Minimized window."
    elif "maximize" in command:
        pyautogui.hotkey('win', 'up')
        return "Maximized window."

    # 4. Application Management (Open/Close)
    elif "open" in command:
        app_name = command.replace("open", "").strip()
        if "google" in app_name:
            webbrowser.open("https://google.com")
            return "Opening Google."
        elif "youtube" in app_name:
            webbrowser.open("https://youtube.com")
            return "Opening YouTube."
        try:
            open_app(app_name, match_closest=True, output=False)
            return f"Opening {app_name}."
        except:
            return f"Could not find {app_name}."
            
    elif "close" in command:
        app_name = command.replace("close", "").strip()
        try:
            close_app(app_name, match_closest=True, output=False)
            return f"Closing {app_name}."
        except:
            return f"Could not close {app_name}."

    # 5. Web Automation
    elif "search for" in command:
        query = command.replace("search for", "").strip()
        pywhatkit.search(query)
        return f"Searching web for {query}."
    elif "play" in command:
        query = command.replace("play", "").strip()
        pywhatkit.playonyt(query)
        return f"Playing {query}."

    # 6. System Status
    elif "time" in command:
        return f"Time: {datetime.now().strftime('%I:%M %p')}."
    elif "date" in command:
        return f"Date: {datetime.now().strftime('%A, %B %d, %Y')}."
    elif "who are you" in command:
        return "I am AURA. System Control Module Online."
    
    # 7. Shutdown
    elif any(word in command for word in ["shutdown", "exit", "bye", "goodbye"]):
        return "Goodbye."
        
    return ""

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Advanced System Control Logic with Smart Command Splitting
    """
    user_message = request.message.lower()
    print(f"Command received: {user_message}")
    
    # List of keywords that start a new command
    keywords = ["open", "close", "play", "search", "type", "press", "send", "shutdown", "exit", "time", "date"]
    
    # 1. Pre-processing: Insert a delimiter before keywords if they appear in the middle
    # Pattern: Look for keywords, but ignore if they are at the start of the string
    # We replace " open " with " | open ", " close " with " | close "
    # We use a unique delimiter "|"
    
    processed_message = user_message
    for word in keywords:
        # Regex to find the word as a whole word, not part of another (e.g. 'opener')
        # And ensure it's not at the very start
        processed_message = re.sub(fr'(?<=\s){word}(?=\s|$)', f'|{word}', processed_message)
        
    # 2. Split by delimiters (and, then, also, comma, period, and our new pipe |)
    raw_commands = re.split(r'\s+(?:and|then|also)\s+|\s*[,.|]\s*', processed_message)
    
    responses = []
    last_verb = None
    
    for cmd in raw_commands:
        cmd = cmd.strip()
        if not cmd:
            continue
            
        # --- Context Inference (Verb Distribution) ---
        parts = cmd.split(' ')
        first_word = parts[0]
        
        # If this command doesn't start with a known action, but we have a context verb
        # Example: "open google whatsapp" -> "open google" (processed) -> "whatsapp" (next cmd)
        # With the split logic above, "open google whatsapp" might stay as one if "whatsapp" isn't a keyword.
        # But "open google open whatsapp" becomes "open google", "open whatsapp".
        
        # Handle "open google whatsapp" (implicit list)
        # If the previous command was "open" and this one has no verb, assume "open"
        if first_word not in keywords and last_verb in ["open", "close"]:
            cmd = f"{last_verb} {cmd}"
            print(f"Inferring command: {cmd}")
            
        # Update last_verb
        if first_word in ["open", "close"]:
            last_verb = first_word
        elif first_word in ["play", "search", "send"]:
            last_verb = None 
            
        resp = process_single_command(cmd)
        if resp:
            responses.append(resp)
            
        # Delay for UI/OS stability
        if len(raw_commands) > 1:
            time.sleep(1.0)

    final_response = " ".join(responses)
    if not final_response:
        final_response = "Command processed."

    return {"response": final_response}

# Serve Static Files (Frontend)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("INITIALIZING AURA SYSTEM CONTROL...")
    # Using port 8001 to avoid conflicts
    uvicorn.run(app, host="127.0.0.1", port=8001)
