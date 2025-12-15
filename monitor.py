#!/usr/bin/env python3
# server.py - ArchWay File Server
"""
🚀 ArchWay File Server - Локальный файлообменник для школ и домашних сетей
📱 Работает на Termux (Android) и любом Linux
🎯 Показывает все файлы, кроме служебных
"""

import os
import json
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import sys

class Config:
    """Конфигурация сервера"""
    def __init__(self):
        self.port = 8080
        self.host = '0.0.0.0'
        self.base_folder = os.getcwd()
        
        # ЧТО ИГНОРИРОВАТЬ (папки и файлы)
        self.ignore_folders = ['css', 'js', '__pycache__', '.git', 'node_modules']
        self.ignore_files = [
            'accounts.txt', 'manager.py', 'isos.html',
            'server.py', 'config.json', '.gitignore',
            'README.md', 'LICENSE', 'index.html', 'monitor.py'
        ]
        
        # Расширения для игнорирования
        self.ignore_extensions = ['.pyc', '.log', '.tmp', '.swp']
        
        # Настройки отображения
        self.show_hidden = False
        self.sort_by = 'name'  # name, size, date
        self.sort_reverse = False
        
        # Загружаем из config.json если есть
        self.load_config()
    
    def load_config(self):
        """Загружаем конфигурацию из файла"""
        config_file = Path(self.base_folder) / 'config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.__dict__.update(data)
                    print("✅ Конфигурация загружена из config.json")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки конфигурации: {e}")

class FileManager:
    """Управление файлами и фильтрацией"""
    
    def __init__(self, config):
        self.config = config
        self.base_path = Path(config.base_folder)
    
    def should_ignore(self, item_path):
        """Определяем, нужно ли игнорировать элемент"""
        item_name = item_path.name
        
        # Скрытые файлы (если не включено отображение)
        if not self.config.show_hidden and item_name.startswith('.'):
            return True
        
        # Игнорируемые папки
        if item_path.is_dir() and item_name in self.config.ignore_folders:
            return True
        
        # Игнорируемые файлы
        if item_path.is_file() and item_name in self.config.ignore_files:
            return True
        
        # Игнорируемые расширения
        if item_path.is_file() and item_path.suffix.lower() in self.config.ignore_extensions:
            return True
        
        return False
    
    def get_directory_listing(self, path=None):
        """Получаем список файлов и папок с фильтрацией"""
        if path is None:
            path = self.base_path
        
        items = {
            'folders': [],
            'files': []
        }
        
        try:
            for item in path.iterdir():
                # Пропускаем игнорируемые элементы
                if self.should_ignore(item):
                    continue
                
                # Собираем информацию
                stat = item.stat()
                info = {
                    'name': item.name,
                    'path': str(item.relative_to(self.base_path)),
                    'is_dir': item.is_dir(),
                    'size': stat.st_size if item.is_file() else 0,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'created': datetime.fromtimestamp(stat.st_ctime)
                }
                
                # Добавляем в соответствующую категорию
                if item.is_dir():
                    # Считаем количество файлов в папке
                    try:
                        file_count = sum(1 for f in item.rglob('*') if f.is_file() and not self.should_ignore(f))
                        info['file_count'] = file_count
                    except:
                        info['file_count'] = 0
                    items['folders'].append(info)
                else:
                    items['files'].append(info)
            
            # Сортируем
            if self.config.sort_by == 'name':
                items['folders'].sort(key=lambda x: x['name'].lower(), reverse=self.config.sort_reverse)
                items['files'].sort(key=lambda x: x['name'].lower(), reverse=self.config.sort_reverse)
            elif self.config.sort_by == 'size':
                items['files'].sort(key=lambda x: x['size'], reverse=self.config.sort_reverse)
            elif self.config.sort_by == 'date':
                items['folders'].sort(key=lambda x: x['modified'], reverse=self.config.sort_reverse)
                items['files'].sort(key=lambda x: x['modified'], reverse=self.config.sort_reverse)
            
        except PermissionError:
            print(f"⚠️ Нет доступа к папке: {path}")
        
        return items
    
    def format_size(self, bytes):
        """Форматирует размер файла"""
        if bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"
    
    def get_file_icon(self, filename, is_dir=False):
        """Возвращает иконку для файла/папки"""
        if is_dir:
            return '📁'
        
        ext = Path(filename).suffix.lower()
        icons = {
            '.iso': '💿', '.img': '💿', '.vhd': '💿',
            '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦', '.gz': '📦',
            '.exe': '⚙️', '.msi': '⚙️', '.sh': '⚙️', '.bat': '⚙️',
            '.pdf': '📄', '.txt': '📄', '.doc': '📄', '.docx': '📄',
            '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬', '.mov': '🎬',
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
            '.jpg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.svg': '🖼️',
            '.apk': '📱', '.deb': '🐧', '.rpm': '🐧', '.pkg': '🍎',
            '.html': '🌐', '.css': '🎨', '.js': '📜', '.py': '🐍'
        }
        return icons.get(ext, '📄')

class HTMLGenerator:
    """Генератор HTML страниц"""
    
    def __init__(self, config, file_manager):
        self.config = config
        self.fm = file_manager
    
    def generate_index(self, items, current_path=''):
        """Генерирует главную страницу"""
        
        # Генерируем список папок
        folders_html = ''
        for folder in items['folders']:
            folders_html += f'''
            <div class="item folder">
                <div class="icon">📁</div>
                <div class="info">
                    <a href="{folder['path']}/" class="name">{folder['name']}/</a>
                    <div class="meta">
                        <span class="files">{folder['file_count']} файлов</span>
                        <span class="date">{folder['modified'].strftime('%Y-%m-%d %H:%M')}</span>
                    </div>
                </div>
            </div>
            '''
        
        # Генерируем список файлов
        files_html = ''
        for file in items['files']:
            icon = self.fm.get_file_icon(file['name'])
            size = self.fm.format_size(file['size'])
            
            files_html += f'''
            <div class="item file">
                <div class="icon">{icon}</div>
                <div class="info">
                    <a href="{file['path']}" class="name" download>{file['name']}</a>
                    <div class="meta">
                        <span class="size">{size}</span>
                        <span class="date">{file['modified'].strftime('%Y-%m-%d %H:%M')}</span>
                    </div>
                </div>
                <a href="{file['path']}" class="download-btn" download>⬇️</a>
            </div>
            '''
        
        # Общая статистика
        total_files = len(items['files'])
        total_size = sum(f['size'] for f in items['files'])
        total_size_str = self.fm.format_size(total_size)
        
        # HTML шаблон
        html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ArchWay File Server - {current_path or 'Главная'}</title>
    <style>
        :root {{
            --primary: #00ff00;
            --bg: #0a0a0a;
            --card: #111111;
            --text: #ffffff;
            --text-secondary: #888888;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            background: var(--bg);
            color: var(--text);
            font-family: 'Courier New', monospace;
            line-height: 1.6;
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid var(--primary);
            margin-bottom: 30px;
        }}
        
        h1 {{
            color: var(--primary);
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 0 0 10px var(--primary);
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1em;
        }}
        
        .stats {{
            background: var(--card);
            border: 1px solid var(--primary);
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            text-align: center;
        }}
        
        .items-list {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin: 20px 0;
        }}
        
        .item {{
            background: var(--card);
            border: 1px solid rgba(0, 255, 0, 0.3);
            padding: 15px;
            border-radius: 5px;
            display: flex;
            align-items: center;
            gap: 15px;
            transition: all 0.3s;
        }}
        
        .item:hover {{
            border-color: var(--primary);
            box-shadow: 0 0 15px rgba(0, 255, 0, 0.2);
            transform: translateY(-2px);
        }}
        
        .item.folder {{
            border-left: 5px solid #ff9900;
        }}
        
        .item.file {{
            border-left: 5px solid var(--primary);
        }}
        
        .icon {{
            font-size: 2em;
            flex-shrink: 0;
        }}
        
        .info {{
            flex-grow: 1;
        }}
        
        .name {{
            color: var(--primary);
            font-size: 1.1em;
            text-decoration: none;
            display: block;
            margin-bottom: 5px;
            word-break: break-all;
        }}
        
        .name:hover {{
            color: #ffff00;
        }}
        
        .meta {{
            display: flex;
            gap: 15px;
            color: var(--text-secondary);
            font-size: 0.9em;
        }}
        
        .download-btn {{
            background: transparent;
            color: var(--primary);
            border: 2px solid var(--primary);
            padding: 8px 15px;
            border-radius: 3px;
            text-decoration: none;
            font-size: 1.2em;
            transition: all 0.3s;
            flex-shrink: 0;
        }}
        
        .download-btn:hover {{
            background: var(--primary);
            color: var(--bg);
        }}
        
        .breadcrumb {{
            margin: 15px 0;
            color: var(--text-secondary);
        }}
        
        .breadcrumb a {{
            color: var(--primary);
            text-decoration: none;
        }}
        
        .breadcrumb a:hover {{
            text-decoration: underline;
        }}
        
        footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--text-secondary);
            color: var(--text-secondary);
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .item {{
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }}
            
            .download-btn {{
                align-self: flex-end;
                margin-top: 10px;
            }}
            
            .meta {{
                flex-direction: column;
                gap: 5px;
            }}
        }}
        
        /* Эффект ЭЛТ монитора */
        .crt-effect {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            background: linear-gradient(
                rgba(18, 16, 16, 0) 50%,
                rgba(0, 0, 0, 0.25) 50%
            );
            background-size: 100% 4px;
            z-index: 9999;
        }}
    </style>
</head>
<body>
    <div class="crt-effect"></div>
    
    <div class="container">
        <header>
            <h1>🦾 ArchWay File Server</h1>
            <div class="subtitle">Локальный файлообменник • Порт: {self.config.port}</div>
        </header>
        
        <div class="stats">
            📊 Файлов: {total_files} • 📦 Общий размер: {total_size_str} • 🕐 {datetime.now().strftime('%H:%M:%S')}
        </div>
        
        <div class="breadcrumb">
            <a href="/">Главная</a>
            {f" / {current_path}" if current_path else ""}
        </div>
        
        <div class="items-list">
            {folders_html}
            {files_html}
        </div>
        
        <footer>
            <p>ArchWay File Server • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Папка: {self.config.base_folder}</p>
            <p>Сервер запущен на http://localhost:{self.config.port}</p>
        </footer>
    </div>
    
    <script>
        // Автообновление каждые 30 секунд
        setTimeout(function() {{
            location.reload();
        }}, 30000);
        
        // Показываем полное имя файла при наведении
        document.querySelectorAll('.name').forEach(el => {{
            el.title = el.textContent;
        }});
        
        // Добавляем эффект печатающего текста в заголовке
        const title = document.querySelector('h1');
        const originalText = title.textContent;
        title.textContent = '';
        
        let i = 0;
        function typeWriter() {{
            if (i < originalText.length) {{
                title.textContent += originalText.charAt(i);
                i++;
                setTimeout(typeWriter, 50);
            }}
        }}
        
        // Запускаем после загрузки страницы
        window.addEventListener('load', typeWriter);
    </script>
</body>
</html>'''
        
        return html

class ArchWayHTTPHandler(SimpleHTTPRequestHandler):
    """Обработчик HTTP запросов"""
    
    def __init__(self, *args, **kwargs):
        self.config = Config()
        self.fm = FileManager(self.config)
        self.html_gen = HTMLGenerator(self.config, self.fm)
        super().__init__(*args, directory=self.config.base_folder, **kwargs)
    
    def do_GET(self):
        """Обрабатываем GET запросы"""
        # Блокируем доступ к игнорируемым файлам
        requested_path = self.path.lstrip('/')
        if requested_path in self.config.ignore_files:
            self.send_error(403, "Access to this file is forbidden")
            return
        
        # Генерируем индекс для корня
        if self.path == '/' or self.path.endswith('/'):
            items = self.fm.get_directory_listing()
            html = self.html_gen.generate_index(items, self.path.strip('/'))
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        else:
            # Отдаём файлы как обычно
            super().do_GET()
    
    def log_message(self, format, *args):
        """Кастомное логирование"""
        client_ip = self.client_address[0]
        print(f"🌐 {datetime.now().strftime('%H:%M:%S')} - {client_ip} - {format%args}")

def main():
    """Главная функция"""
    config = Config()
    
    print("\n" + "="*60)
    print("🦾 ARCHWAY FILE SERVER v1.0")
    print("="*60)
    print(f"📁 Папка сервера: {config.base_folder}")
    print(f"🌐 Локальный адрес: http://localhost:{config.port}")
    print(f"📡 Сетевой адрес: http://<ваш-ip>:{config.port}")
    print("="*60)
    print("🚫 Игнорируемые папки: " + ", ".join(config.ignore_folders))
    print("🚫 Игнорируемые файлы: " + ", ".join(config.ignore_files[:3]) + "...")
    print("="*60)
    print("🚀 Сервер запускается...")
    
    try:
        server = HTTPServer((config.host, config.port), ArchWayHTTPHandler)
        print(f"✅ Сервер запущен на порту {config.port}")
        print("📱 Откройте браузер и перейдите по указанному адресу")
        print("🛑 Для остановки нажмите Ctrl+C")
        print("="*60 + "\n")
        
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен")
        server.server_close()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Порт {config.port} уже занят!")
            print("🔄 Используйте другой порт:")
            print("   python server.py --port 8081")
        else:
            print(f"❌ Ошибка: {e}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    main()
