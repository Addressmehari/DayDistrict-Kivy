
# Common imports are assumed to be in screens.py already or will be added.
# New imports for Web Server
import http.server
import socketserver
import threading
import os
import shutil
from kivy.utils import platform
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

# Load KV
Builder.load_file("map_screen.kv")

# Server Configuration
PORT = 8080
SERVER_STARTED = False

def setup_www_dir():
    # 1. Determine Bundle Directory (Source)
    # On Android, this is where the APK extracts assets
    app_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(app_dir, "GitVille")

    # 2. Determine Writable Directory (Target)
    if platform == 'android':
        app = App.get_running_app()
        data_dir = app.user_data_dir
        # Fallback if app is not ready yet? usually ready in main loop
        if not data_dir: 
            data_dir = "/data/data/org.test.diaryapp/files"
    else:
        # On Windows/Desktop, use same pattern for consistency or just temp
        # But to match DiaryManager's "data_dir" logic:
        data_dir = app_dir

    target_dir = os.path.join(data_dir, "GitVille_www")
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # 3. Copy Static Assets (HTML, JS, CSS)
    # We copy them every time to update if app updates
    # We skip houses.json/roads.json if they exist? No, generator handles them.
    # Actually generator runs on save. On first launch, they might be missing.
    
    if os.path.exists(source_dir):
        for item in os.listdir(source_dir):
            s = os.path.join(source_dir, item)
            d = os.path.join(target_dir, item)
            
            # Don't overwrite dynamic data if it exists?
            # houses.json and roads.json are dynamic.
            if item in ["houses.json", "roads.json"]:
                if not os.path.exists(d): 
                    # If missing, copy defaults/empty
                    if os.path.isfile(s):
                         shutil.copy2(s, d)
                continue
                
            if os.path.isfile(s):
                shutil.copy2(s, d)
            # Recursive copy for dirs if any?
    else:
        print(f"Source GitVille dir not found at {source_dir}")

    return target_dir


def start_local_server():
    global SERVER_STARTED
    if SERVER_STARTED:
        return

    # Setup the serving directory
    web_dir = setup_www_dir()
    
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
             # Allow reuse address to prevent "Address already in use" on restarts
            socketserver.TCPServer.allow_reuse_address = True
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
create_webview = None
remove_webview = None
webview_import_error = None

if platform == 'android':
    try:
        from jnius import autoclass, cast, PythonJavaClass, java_method
        from android.runnable import run_on_ui_thread
        
        WebView = autoclass('android.webkit.WebView')
        WebViewClient = autoclass('android.webkit.WebViewClient')
        # Use FrameLayout.LayoutParams for margins
        LayoutParams = autoclass('android.widget.FrameLayout$LayoutParams')
        TypedValue = autoclass('android.util.TypedValue')
        activity = autoclass('org.kivy.android.PythonActivity').mActivity
        
        class MyWebViewClient(WebViewClient):
            pass
            
        @run_on_ui_thread
        def _create_webview_impl(url):
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
            
            # Layout Params to fill screen minus navbar (85dp to be safe? 80dp is bar)
            params = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT)
            
            # Calculate Bottom Margin (80dp) in Pixels
            try:
                metrics = activity.getResources().getDisplayMetrics()
                # 1 = COMPLEX_UNIT_DIP
                bottom_margin_px = int(TypedValue.applyDimension(1, 80.0, metrics))
                params.setMargins(0, 0, 0, bottom_margin_px)
            except Exception as e:
                print(f"Margin calc error: {e}")
            
            activity.addContentView(webview, params)
            
            webview_obj = webview
            webview_attached = True
            
        @run_on_ui_thread
        def _remove_webview_impl():
            global webview_obj, webview_attached
            if webview_obj and webview_attached:
                # Remove from parent
                parent = webview_obj.getParent()
                if parent:
                    parent.removeView(webview_obj)
                webview_obj = None
                webview_attached = False

        # Assign to global variables
        create_webview = _create_webview_impl
        remove_webview = _remove_webview_impl

    except Exception as e:
        print(f"Android Import Error: {e}")
        webview_import_error = str(e)

class CityMapScreen(Screen):
    def on_enter(self):
        start_local_server()
        url = f"http://localhost:{PORT}/index.html"
        
        if platform == 'android':
            if create_webview:
                try:
                    create_webview(url)
                except Exception as e:
                    self.ids.status_full.text = f"Error launching Webview: {e}"
            else:
                self.ids.status_full.text = f"Webview init failed: {webview_import_error}"
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
        if platform == 'android' and remove_webview:
             try:
                 remove_webview()
             except:
                 pass
