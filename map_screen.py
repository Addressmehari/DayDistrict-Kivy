
# Common imports are assumed to be in screens.py already or will be added.
# New imports for Web Server
import http.server
import socketserver
import threading
import os
from kivy.utils import platform
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

# Load KV
Builder.load_file("map_screen.kv")

# Server Configuration
PORT = 8080
SERVER_STARTED = False

def start_local_server():
    global SERVER_STARTED
    if SERVER_STARTED:
        return

    # Use absolute path to GitVille
    app_dir = os.path.dirname(os.path.abspath(__file__))
    web_dir = os.path.join(app_dir, "GitVille")
    
    if not os.path.exists(web_dir):
        print(f"Error: Web directory {web_dir} not found.")
        return

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=web_dir, **kwargs)
        
        def log_message(self, format, *args):
            pass # Silence logs

    def serve():
        try:
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                print(f"Local Server running at http://localhost:{PORT}")
                httpd.serve_forever()
        except OSError as e:
            print(f"Server error (Port {PORT} maybe in use): {e}")

    t = threading.Thread(target=serve, daemon=True)
    t.start()
    SERVER_STARTED = True

# Android Native WebView Logic
webview_attached = False
webview_obj = None

if platform == 'android':
    try:
        from jnius import autoclass, cast, PythonJavaClass, java_method
        from android.runnable import run_on_ui_thread
        
        WebView = autoclass('android.webkit.WebView')
        WebViewClient = autoclass('android.webkit.WebViewClient')
        LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
        activity = autoclass('org.kivy.android.PythonActivity').mActivity
        
        class MyWebViewClient(WebViewClient):
            pass
            
        @run_on_ui_thread
        def create_webview(url):
            global webview_obj, webview_attached
            if webview_obj:
                webview_obj.loadUrl(url)
                return

            webview = WebView(activity)
            settings = webview.getSettings()
            settings.setJavaScriptEnabled(True)
            settings.setDomStorageEnabled(True)
            settings.setAllowFileAccess(True)
            
            webview.setWebViewClient(MyWebViewClient())
            webview.loadUrl(url)
            
            # Layout Params to fill screen (minus navbar if possible, or full)
            # For simplicity, we fill parent. In a real app, we might want to attach to a 
            # specific layout container ID, but Kivy controls the window.
            # We add to the main DecorView.
            
            params = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT)
            
            # Correction: Attaching to Window directly overlays EVERYTHING (including Kivy UI).
            # This is okay for a "Full Screen Map Tab".
            # We must remove it when switching tabs.
            activity.addContentView(webview, params)
            
            webview_obj = webview
            webview_attached = True
            
        @run_on_ui_thread
        def remove_webview():
            global webview_obj, webview_attached
            if webview_obj and webview_attached:
                # Remove from parent
                parent = webview_obj.getParent()
                if parent:
                    parent.removeView(webview_obj)
                webview_obj = None
                webview_attached = False

    except Exception as e:
        print(f"Android Import Error: {e}")

class CityMapScreen(Screen):
    def on_enter(self):
        start_local_server()
        url = f"http://localhost:{PORT}/index.html"
        
        if platform == 'android':
            try:
                create_webview(url)
            except Exception as e:
                self.ids.status_full.text = f"Error launching Webview: {e}"
        else:
            # Windows / Desktop
            # Try to launch Chrome/Edge in App Mode (Frameless window)
            import shutil
            import subprocess
            
            self.ids.status_full.text = "Attempting to launch embedded window..."
            
            # Common paths for browsers
            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            edge_path = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
            
            browser_exe = None
            if os.path.exists(chrome_path):
                browser_exe = chrome_path
            elif os.path.exists(edge_path):
                browser_exe = edge_path
                
            if browser_exe:
                 # Launch app mode
                 subprocess.Popen([browser_exe, f"--app={url}", "--window-size=1000,800"])
            else:
                 # Fallback
                 import webbrowser
                 self.ids.status_full.text = "Visualizer opened in default browser."
                 webbrowser.open(url)

    def on_leave(self):
        if platform == 'android':
             try:
                 remove_webview()
             except:
                 pass
