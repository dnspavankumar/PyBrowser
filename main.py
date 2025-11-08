import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolBar, QLineEdit, QTabWidget, QMessageBox, QSplashScreen, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor, QFont


class PavanBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PavanBrowser")
        self.homepage_file = Path("homepage.html").resolve()
        self.home_url = f"file:///{self.homepage_file.as_posix()}"
        self.history_file = Path("browser_history.json")
        self.cache_dir = Path("cache")
        self.history = []
        
        # Set window icon
        if Path("browser.png").exists():
            self.setWindowIcon(QIcon("browser.png"))
        
        # Apply dark mode style
        self.apply_dark_mode()
        
        # Create cache directory
        self.cache_dir.mkdir(exist_ok=True)
        
        # Setup web engine profile with persistent storage
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setCachePath(str(self.cache_dir / "cache"))
        self.profile.setPersistentStoragePath(str(self.cache_dir / "storage"))
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        
        # Load history from file
        self.load_history()
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        
        # Set as central widget
        self.setCentralWidget(self.tabs)
        
        # Create navigation toolbar and menu
        self.create_navigation_bar()
        self.create_menu_bar()
        
        # Add initial tab
        self.add_new_tab()
        
        # Show full screen
        self.showFullScreen()
    
    def apply_dark_mode(self):
        dark_stylesheet = """
            QMainWindow {
                background-color: #000000;
            }
            QToolBar {
                background-color: #2b2b2b;
                border: none;
                spacing: 5px;
                padding: 5px;
            }
            QToolButton {
                color: #ffffff;
                background-color: #2b2b2b;
                border: none;
                padding: 5px;
                font-size: 16px;
            }
            QToolButton:hover {
                background-color: #3d3d3d;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px;
            }
            QTabWidget::pane {
                border: none;
                background-color: #000000;
            }
            QTabBar::tab {
                background-color: #2b2b2b;
                color: #888888;
                padding: 8px 15px;
                border: none;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3d3d3d;
                color: #4a9eff;
            }
            QTabBar::tab:hover {
                background-color: #3d3d3d;
            }
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMenuBar::item:selected {
                background-color: #3d3d3d;
            }
            QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
            QMessageBox {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMessageBox QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QMessageBox QPushButton:hover {
                background-color: #4a9eff;
            }
        """
        self.setStyleSheet(dark_stylesheet)
    
    def create_navigation_bar(self):
        navbar = QToolBar()
        self.addToolBar(navbar)
        
        # Back button
        self.back_btn = QAction("←", self)
        self.back_btn.triggered.connect(self.navigate_back)
        navbar.addAction(self.back_btn)
        
        # Forward button
        self.forward_btn = QAction("→", self)
        self.forward_btn.triggered.connect(self.navigate_forward)
        navbar.addAction(self.forward_btn)
        
        # Reload button
        self.reload_btn = QAction("⟳", self)
        self.reload_btn.triggered.connect(self.navigate_reload)
        navbar.addAction(self.reload_btn)
        
        # Home button
        self.home_btn = QAction("🏠", self)
        self.home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(self.home_btn)
        
        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)
        
        # New tab button
        new_tab_btn = QAction("+", self)
        new_tab_btn.triggered.connect(lambda: self.add_new_tab())
        navbar.addAction(new_tab_btn)
    
    def add_new_tab(self, url=None):
        if url is None:
            url = self.home_url
        
        browser = QWebEngineView()
        
        # Create custom page with error handling
        page = QWebEnginePage(self.profile, browser)
        browser.setPage(page)
        
        browser.setUrl(QUrl(url))
        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_url_bar(qurl, browser))
        browser.loadFinished.connect(lambda success, browser=browser: self.handle_load_finished(success, browser))
        browser.loadFinished.connect(lambda _, browser=browser: self.update_tab_title(browser))
        browser.loadFinished.connect(lambda _, browser=browser: self.add_to_history(browser.url()))
        browser.loadFinished.connect(lambda _, browser=browser: self.sync_history_to_page(browser))
        
        index = self.tabs.addTab(browser, "New Tab")
        self.tabs.setCurrentIndex(index)
        
        return browser
    
    def handle_load_finished(self, success, browser):
        """Handle page load errors"""
        if not success:
            url = browser.url().toString()
            if url and not url.startswith("file:///"):
                error_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                        }}
                        .error-container {{
                            text-align: center;
                            padding: 40px;
                            background: rgba(0,0,0,0.3);
                            border-radius: 15px;
                            max-width: 600px;
                        }}
                        h1 {{ font-size: 48px; margin-bottom: 20px; }}
                        p {{ font-size: 18px; margin-bottom: 30px; }}
                        .url {{ 
                            background: rgba(255,255,255,0.2);
                            padding: 10px;
                            border-radius: 5px;
                            word-break: break-all;
                            margin: 20px 0;
                        }}
                        button {{
                            background: #4a9eff;
                            color: white;
                            border: none;
                            padding: 12px 30px;
                            font-size: 16px;
                            border-radius: 25px;
                            cursor: pointer;
                            margin: 5px;
                        }}
                        button:hover {{ background: #3d8ae6; }}
                    </style>
                </head>
                <body>
                    <div class="error-container">
                        <h1>⚠️ Page Not Found</h1>
                        <p>Unable to load the requested page</p>
                        <div class="url">{url}</div>
                        <p>Please check the URL and try again</p>
                        <button onclick="window.history.back()">Go Back</button>
                        <button onclick="window.location.href='about:blank'">Home</button>
                    </div>
                </body>
                </html>
                """
                browser.setHtml(error_html)
    
    def close_tab(self, index):
        if self.tabs.count() > 1:
            browser = self.tabs.widget(index)
            self.tabs.removeTab(index)
            browser.deleteLater()
        else:
            self.close()
    
    def current_tab_changed(self, index):
        if index >= 0:
            browser = self.tabs.currentWidget()
            if browser:
                self.update_url_bar(browser.url(), browser)
    
    def get_current_browser(self):
        return self.tabs.currentWidget()
    
    def navigate_back(self):
        browser = self.get_current_browser()
        if browser:
            browser.back()
    
    def navigate_forward(self):
        browser = self.get_current_browser()
        if browser:
            browser.forward()
    
    def navigate_reload(self):
        browser = self.get_current_browser()
        if browser:
            browser.reload()
    
    def navigate_home(self):
        browser = self.get_current_browser()
        if browser:
            browser.setUrl(QUrl(self.home_url))
    
    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        browser = self.get_current_browser()
        if browser:
            browser.setUrl(QUrl(url))
    
    def update_url_bar(self, url, browser):
        if browser == self.get_current_browser():
            self.url_bar.setText(url.toString())
    
    def update_tab_title(self, browser):
        index = self.tabs.indexOf(browser)
        if index >= 0:
            title = browser.page().title()
            if title:
                self.tabs.setTabText(index, title[:20])
            else:
                self.tabs.setTabText(index, "New Tab")
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # History menu
        self.history_menu = menubar.addMenu("History")
        self.update_history_menu()
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        
        clear_cache_action = QAction("Clear Cache", self)
        clear_cache_action.triggered.connect(self.clear_cache)
        settings_menu.addAction(clear_cache_action)
        
        clear_cookies_action = QAction("Clear Cookies", self)
        clear_cookies_action.triggered.connect(self.clear_cookies)
        settings_menu.addAction(clear_cookies_action)
        
        settings_menu.addSeparator()
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        settings_menu.addAction(about_action)
    
    def update_history_menu(self):
        self.history_menu.clear()
        
        for entry in reversed(self.history[-50:]):
            url = entry["url"]
            title = entry.get("title", url)
            timestamp = entry.get("timestamp", "")
            
            action = QAction(f"{title[:50]} - {timestamp}", self)
            action.triggered.connect(lambda checked, url=url: self.add_new_tab(url))
            self.history_menu.addAction(action)
    
    def add_to_history(self, qurl):
        url = qurl.toString()
        if url and url != "about:blank" and not url.startswith("file:///"):
            browser = self.get_current_browser()
            title = browser.page().title() if browser else url
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            entry = {
                "url": url,
                "title": title,
                "timestamp": timestamp
            }
            
            self.history.append(entry)
            self.save_history()
            self.update_history_menu()
    
    def sync_history_to_page(self, browser):
        """Sync history to the homepage's localStorage"""
        if browser.url().toString().startswith("file:///"):
            history_json = json.dumps(self.history)
            script = f"localStorage.setItem('browserHistory', '{history_json}');"
            browser.page().runJavaScript(script)
    
    def load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []
        else:
            self.history = []
    
    def save_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def clear_cache(self):
        self.profile.clearHttpCache()
        cache_path = Path(self.profile.cachePath())
        if cache_path.exists():
            try:
                shutil.rmtree(cache_path)
                cache_path.mkdir(exist_ok=True)
            except Exception:
                pass
        QMessageBox.information(self, "Cache Cleared", "Browser cache has been cleared successfully.")
    
    def clear_cookies(self):
        self.profile.cookieStore().deleteAllCookies()
        QMessageBox.information(self, "Cookies Cleared", "All cookies have been cleared successfully.")
    
    def show_about(self):
        QMessageBox.about(
            self,
            "About PavanBrowser",
            "PavanBrowser v1.0\n\nBuilt from scratch in Python"
        )


def create_splash_screen():
    """Create a splash screen for startup"""
    pixmap = QPixmap(600, 400)
    pixmap.fill(QColor("#1e3c72"))
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Draw title
    painter.setPen(QColor("#ffffff"))
    font = QFont("Arial", 36, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "PavanBrowser")
    
    # Draw subtitle
    font = QFont("Arial", 14)
    painter.setFont(font)
    painter.setPen(QColor("#cccccc"))
    painter.drawText(50, 250, 500, 50, Qt.AlignmentFlag.AlignCenter, "Launching PavanBrowser...")
    
    # Draw version
    font = QFont("Arial", 10)
    painter.setFont(font)
    painter.drawText(50, 350, 500, 30, Qt.AlignmentFlag.AlignCenter, "v1.0 - Built from scratch in Python")
    
    painter.end()
    
    splash = QSplashScreen(pixmap)
    splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
    return splash


def main():
    app = QApplication(sys.argv)
    
    # Show splash screen
    splash = create_splash_screen()
    splash.show()
    app.processEvents()
    
    # Simulate loading time
    QTimer.singleShot(1500, lambda: None)
    app.processEvents()
    
    # Create main window
    window = PavanBrowser()
    
    # Close splash and show window
    splash.finish(window)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
