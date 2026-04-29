#!/usr/bin/env python3
import os
import json
import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

class Config:
    def __init__(self, base_folder=None):
        self.port = 8080
        self.host = '0.0.0.0'
        self.base_folder = os.path.abspath(base_folder or os.getcwd())
        self.ignore_folders = ['css', 'js', '__pycache__', '.git', 'node_modules', 'System32', 'SysWOW64', 'Windows', '$Recycle.Bin', 'Program Files', 'ProgramData', 'AppData']

def main():
    parser = argparse.ArgumentParser(description="ArchWay File Server")
    parser.add_argument('--port', '-p', type=int, default=8080, help='Порт сервера')
    parser.add_argument('--folder', '-f', default=None, help='Папка для хостинга')
    args = parser.parse_args()

    config = Config(base_folder=args.folder)

    class CustomHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=config.base_folder, **kwargs)

    print(f"🚀 Запуск на порту {args.port}")
    print(f"📁 Хостим папку: {config.base_folder}")

    server = HTTPServer((config.host, args.port), CustomHandler)
    server.serve_forever()

if __name__ == "__main__":
    main()
