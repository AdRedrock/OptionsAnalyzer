import os
import sys
import time
import setproctitle
import requests
import json
import socket

from pathlib import Path
from multiprocessing import Process, Condition

from PySide6.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt

from launch import run_dash
from system.process_manager import terminate_when_process_dies
from system.file_paths import get_global_dir

base_dir = os.path.dirname(os.path.abspath(__file__))
logo_dir = os.path.join(base_dir, 'assets', 'logo')
icon_path_png = os.path.abspath(os.path.join(logo_dir, 'options_analyzer_256.png'))
ico_path = os.path.abspath(os.path.join(logo_dir, 'options_analyzer_256.ico'))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Options Analyzer")
        self.setGeometry(100, 100, 1280, 720)
        

        if os.path.exists(ico_path):
            self.app_icon = QIcon(ico_path)
            self.setWindowIcon(self.app_icon)
            QApplication.instance().setWindowIcon(self.app_icon)
            
            self.setWindowIcon(QIcon(ico_path))

            self.tray = QSystemTrayIcon(self)
            self.tray.setIcon(self.app_icon)
            
            self.tray_menu = QMenu()
            
            show_action = QAction("Afficher", self)
            show_action.triggered.connect(self.show)
            self.tray_menu.addAction(show_action)

            hide_action = QAction("Masquer", self)
            hide_action.triggered.connect(self.hide)
            self.tray_menu.addAction(hide_action)
            
            self.tray_menu.addSeparator()
            
            quit_action = QAction("Quitter", self)
            quit_action.triggered.connect(QApplication.instance().quit)
            self.tray_menu.addAction(quit_action)

            self.tray.setContextMenu(self.tray_menu)
            
            self.tray.show()

            self.tray.activated.connect(self.onTrayIconActivated)

        self.web = QWebEngineView()

        custom_style = """
            ::-webkit-scrollbar {
                width: 10px;
                height: 10px;
            }
            
            ::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 5px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 5px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #555;
            }
        """
    
        self.web.page().setHtml(f"""
            <html>
                <head>
                    <style>{custom_style}</style>
                </head>
                <body>
                    <script>
                        window.location.href = 'http://127.0.0.1:8050/metrics';
                    </script>
                </body>
            </html>
        """)
        
        settings = self.web.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)

        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        profile = self.web.page().profile()
        cache_path = "./cache"  
        profile.setCachePath(cache_path)
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        
        self.setCentralWidget(self.web)
        self.web.setZoomFactor(1.05)
        
        try:
            self.set_custom_title_bar((255, 0, 0))
        except:
            pass

    def closeEvent(self, event):
        """Tray system Close"""
        if hasattr(self, 'tray'):
            self.tray.hide()  
            self.tray.deleteLater()  

        event.accept() 
        QApplication.quit()

    def onTrayIconActivated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def set_custom_title_bar(self, color=(128, 0, 128)):
        if sys.platform != "win32":
            return  



def wait_for_server(host: str, port: int, max_retries: int = 50) -> bool:
    """Waits for Dash server to be accessible"""
    url = f"http://{host}:{port}/metrics"  
    for i in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.ConnectionError:
            if i < max_retries - 1:  
                print(f"Connection attempt {i+1}/{max_retries}...")
            time.sleep(0.2)  
    return False

def find_available_port(localhost, start_port=8050, max_attempts=100):
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((localhost, port)) != 0:  
                return port  
    return None

def connection():
    file_path = (get_global_dir() / 'user_config' / 'server_settings.json')

    localhost = '127.0.0.1'
    port = 8050  

    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Using default settings.")
    else:
        try:
            with open(file_path, 'r') as f:
                server_data = json.load(f)
                localhost = server_data.get('localhost', '127.0.0.1')
                
                port = server_data.get('port', 8050)
                if not isinstance(port, int):
                    print(f"Warning: Invalid port '{port}' found in config. Using default 8050.")
                    port = 8050  
        except json.JSONDecodeError:
            print("Error decoding JSON file. Using default settings.")
        except Exception as e:
            print(f"Unknown error: {e}. Using default settings.")

    available_port = find_available_port(localhost, port)
    
    if available_port is None:
        print("No available ports found in the range.")
        return None, None
    
    print(f"Using port {available_port}")
    return localhost, available_port



def run():

    host, port = connection()

    server_is_started = Condition()

    setproctitle.setproctitle('OptionsAnalyzer')

    p = Process(target=run_dash, args=(host, port, server_is_started))
    p.start()

    with server_is_started:
        print("Waiting the Dash server")
        server_is_started.wait(timeout=1)  
    
    if not wait_for_server(host, port):
        print("Error : unable to connect to Dash server")
        p.terminate()
        sys.exit(1)
    
    print("The Dash server is ready !")

    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1.5"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "Round"

    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        "--enable-webgl "
        "--disable-gpu-compositing"
        "--enable-accelerated-2d-canvas "
        "--enable-gpu-rasterization "
        "--ignore-gpu-blocklist "
        "--enable-native-gpu-memory-buffers "
        "--num-raster-threads=4 "
        "--enable-zero-copy "
        "--enable-accelerated-video-decode"
    )
    
    qt_app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    try:
        exit_code = qt_app.exec()
    finally:
        p.terminate()
        sys.exit(exit_code)

if __name__ == '__main__':
    run()
