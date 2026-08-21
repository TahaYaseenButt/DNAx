import sys
import os
import subprocess
import shutil
import tkinter as tk
from tkinter import messagebox
from navigation import NavigationFrame
from pages.home import HomePage
from tools.size_calc import SizeCalculatorPage
from pages.comparator import ComparatorPage
from pages.protocol import ProtocolPage
from tools.primer_designer import PrimerDesignerPage
from pages.validation import ValidationPage
from ui_widgets import NavButton
from tools.dna_generate import DNAGeneratePage
from tools.qpcr import QPCRPage # Import QPCRPage
from pages.matrix_db import MatrixDBPage # Import MatrixDBPage
from pages.export import ExportPage # Import ExportPage
from utils import run_uninstaller


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DNAₓ Lab")
        
        # Set App ID to ensure Windows taskbar groups and shows the custom icon correctly
        try:
            import ctypes
            myappid = 'dnax.lab.app.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

        # Start maximized (keeps Windows taskbar and window decorations).
        # F11 toggles maximize; Escape restores window.
        self.maximized = True
        try:
            self.state('zoomed')
        except Exception:
            # fallback to screen-size geometry if zoomed isn't supported
            try:
                w = self.winfo_screenwidth()
                h = self.winfo_screenheight()
                self.geometry(f"{w}x{h}+0+0")
            except Exception:
                self.geometry("900x600")
        # keep native window decorations so taskbar and native controls behave normally
        try:
            self.overrideredirect(False)
        except Exception:
            pass
        self.bind('<F11>', lambda e: self._toggle_maximize())
        self.bind('<Escape>', lambda e: self._restore())

        self._build_ui()

    def _build_ui(self):
        # Single native title bar is used; place content in row 0
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # attempt to locate a title/logo image in assets and remember path
        # assets are expected to be at 'assets' relative to the bundle root
        from utils import resource_path
        assets_dir = resource_path('assets')
        
        try:
            os.makedirs(assets_dir, exist_ok=True)
        except Exception:
            pass
        title_logo = None
        for fn in ('dnax.png', 'dnax_logo.png', 'logo.png'):
            p = os.path.join(assets_dir, fn)
            if os.path.exists(p):
                title_logo = p
                break
        self._title_logo_path = title_logo

        # set window icon (appears on native title bar) using the logo if available
        # remove the window title text so only the icon shows
        try:
            self.title("DNAx Lab")
        except Exception:
            pass

        if self._title_logo_path:
            try:
                from PIL import Image, ImageTk
                # create an .ico file with multiple sizes for better titlebar rendering on Windows
                ico_path = os.path.join(assets_dir, 'dnax.ico')
                try:
                    if not os.path.exists(ico_path):
                        base = Image.open(self._title_logo_path).convert('RGBA')
                        sizes = [(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)]
                        icons = [base.resize(s, Image.LANCZOS) for s in sizes]
                        icons[0].save(ico_path, format='ICO', sizes=[s for s in sizes])
                except Exception:
                    ico_path = None

                # on Windows prefer .ico via iconbitmap which sets taskbar icon better
                if sys.platform == 'win32' and ico_path and os.path.exists(ico_path):
                    try:
                        self.iconbitmap(default=ico_path)
                    except Exception:
                        pass
                
                # set iconphoto as fallback or for other windows
                imgs = []
                for s in (96,64,48,32):
                    try:
                        img = Image.open(self._title_logo_path).convert('RGBA')
                        img = img.resize((s,s), Image.LANCZOS)
                        imgs.append(ImageTk.PhotoImage(img))
                    except Exception:
                        continue
                if imgs:
                    try:
                        self.iconphoto(True, *imgs)
                        self._icon_images = imgs
                    except Exception:
                        try:
                            self.iconphoto(True, imgs[0])
                            self._icon_images = imgs
                        except Exception:
                            pass
            except Exception:
                try:
                    img = tk.PhotoImage(file=self._title_logo_path)
                    try:
                        self.iconphoto(True, img)
                        self._icon_images = [img]
                    except Exception:
                        pass
                except Exception:
                    pass

        # Right Main Content Container (col 1)
        self.right_container = tk.Frame(self, bg="#f8fafb")
        self.right_container.grid(row=0, column=1, sticky="nsew")
        self.right_container.grid_rowconfigure(1, weight=1)
        self.right_container.grid_columnconfigure(0, weight=1)

        # Navigation controller
        self.navigate = NavigationFrame(self.right_container, bg="#f8fafb")

        # Top Global Navigation Bar with History (Back / Forward) and Interactive Stepper
        from ui_widgets import TopNavBar
        self.top_nav = TopNavBar(self.right_container, self.navigate)
        self.top_nav.grid(row=0, column=0, sticky="ew")

        # Place navigate pages frame in row 1
        self.navigate.grid(row=1, column=0, sticky="nsew")

        # Side menu frame (col 0)
        self._menu_collapsed = False
        self._menu_expanded_width = 230
        self._menu_collapsed_width = 60
        self.menu = tk.Frame(self, bg="#0f172a", width=self._menu_expanded_width)
        self.menu.grid(row=0, column=0, sticky="ns")
        self.menu.grid_propagate(False)
        self.menu.pack_propagate(False)

        # Brand Header
        header = tk.Frame(self.menu, bg="#0f172a", height=58)
        header.pack(fill="x")
        
        self.btn_toggle = tk.Label(header, text="≡", bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 16), cursor="hand2")
        self.btn_toggle.place(x=0, y=4, width=50, height=48)
        self.btn_toggle.bind("<Button-1>", lambda e: self._toggle_sidebar())
        self.btn_toggle.bind("<Enter>", lambda e: self.btn_toggle.config(bg="#1e293b", fg="#ffffff"))
        self.btn_toggle.bind("<Leave>", lambda e: self.btn_toggle.config(bg="#0f172a", fg="#94a3b8"))

        self.brand_title = tk.Label(header, text="DNAₓ Lab", bg="#0f172a", fg="#f8fafc", font=("Segoe UI", 12, "bold"))
        self.brand_title.place(x=50, y=10)
        
        self.brand_sub = tk.Label(header, text="Assay Suite", bg="#0f172a", fg="#64748b", font=("Segoe UI", 8))
        self.brand_sub.place(x=50, y=30)

        # Split menu into scrollable top (main actions) and bottom (secondary actions)
        menu_top = tk.Frame(self.menu, bg="#0f172a")
        menu_top.pack(fill="both", expand=True, pady=4)

        menu_bottom = tk.Frame(self.menu, bg="#0f172a")
        menu_bottom.pack(side="bottom", fill="x", pady=8)

        self.nav_buttons = {}

        def add_nav(parent, text, icon, page_name):
            btn = NavButton(parent, text=text, icon=icon, page_name=page_name,
                            command=lambda: self.navigate.show(page_name),
                            bg="#0f172a", fg="#94a3b8", width=230)
            btn.pack(fill="x", pady=1)
            self.nav_buttons[page_name] = btn
            return btn

        # Section Header Helper
        def add_section(text):
            lbl = tk.Label(menu_top, text=text, bg="#0f172a", fg="#475569", font=("Segoe UI", 7, "bold"), anchor="w", padx=12)
            lbl.pack(fill="x", pady=(10, 2))
            return lbl

        self.section_headers = []
        
        # Navigation Items
        add_nav(menu_top, "Home Dashboard", "🏠", "home")

        self.section_headers.append(add_section("WORKFLOW PIPELINE"))
        add_nav(menu_top, "1. Size Calculator", "📏", "size")
        add_nav(menu_top, "2. DNA Generate", "🧬", "dna")
        add_nav(menu_top, "3. BLAST Comparator", "⚖", "comparator")
        add_nav(menu_top, "4. Primer Designer", "🧪", "primer")
        add_nav(menu_top, "5. qPCR Analysis", "📊", "qpcr")
        add_nav(menu_top, "6. Review & Save", "💾", "export")

        self.section_headers.append(add_section("DATABASE & MATRIX"))
        add_nav(menu_top, "DNA Matrix & DB", "🗄", "matrix_db")
        add_nav(menu_top, "Protocol", "📄", "protocol")

        add_nav(menu_bottom, "Settings", "⚙", "settings")
        add_nav(menu_bottom, "About", "ℹ", "about")

        # Register listener to highlight active sidebar button on navigation
        self.navigate.register_listener(self._update_sidebar_active)

        # Add pages
        self.navigate.add_page("home", HomePage)

        # Settings and About are simple inline pages here
        class SettingsPage(tk.Frame):
            def __init__(self, parent):
                super().__init__(parent, bg="#f8fafb")
                tk.Label(self, text="Settings", font=("Segoe UI", 18, "bold"), bg="#f8fafb", fg="#0f172a").pack(pady=(20, 5))
                tk.Label(self, text="Application settings and maintenance", bg="#f8fafb", fg="#64748b").pack(pady=5)
                tk.Button(self, text="Uninstall Application", fg="white", bg="#d9534f", font=("Segoe UI", 10, "bold"),
                          padx=16, pady=8, relief="flat", cursor="hand2", command=lambda: self._confirm(parent)).pack(pady=20)

            def _confirm(self, parent):
                from tkinter import messagebox
                if messagebox.askyesno("Uninstall", "Do you want to uninstall this application?"):
                    run_uninstaller(parent)

        class AboutPage(tk.Frame):
            def __init__(self, parent):
                super().__init__(parent, bg="#f8fafb")
                tk.Label(self, text="About DNAx Lab", font=("Segoe UI", 18, "bold"), bg="#f8fafb", fg="#0f172a").pack(pady=(20, 5))
                tk.Label(self, text="Production-grade Track & Trace DNA Assay & Authentication Suite.", bg="#f8fafb", fg="#64748b").pack(pady=5)

        self.navigate.add_page("size", SizeCalculatorPage)
        self.navigate.add_page("dna", DNAGeneratePage)
        self.navigate.add_page("matrix_db", MatrixDBPage)
        self.navigate.add_page("comparator", ComparatorPage)
        self.navigate.add_page("primer", PrimerDesignerPage)
        self.navigate.add_page("qpcr", QPCRPage)
        self.navigate.add_page("export", ExportPage)
        self.navigate.add_page("protocol", ProtocolPage)
        self.navigate.add_page("settings", SettingsPage)
        self.navigate.add_page("about", AboutPage)

        # Show initial page
        self.navigate.show("home")

    def _update_sidebar_active(self, current_page, can_back, can_forward):
        """Highlights the active page in sidebar menu."""
        for page_name, btn in self.nav_buttons.items():
            btn.set_active(page_name == current_page)

    def _toggle_sidebar(self):
        """Animate sidebar toggle (Expand <-> Collapse)."""
        step = 25
        delay = 10
        
        target_width = self._menu_collapsed_width if not self._menu_collapsed else self._menu_expanded_width
        current_width = self.menu.winfo_width()
        
        # If collapsing, hide text immediately to prevent clipping ugliness
        if not self._menu_collapsed:
            self.brand_title.place_forget()
            self.brand_sub.place_forget()
            for header_lbl in self.section_headers:
                header_lbl.pack_forget()
            for btn in self.nav_buttons.values():
                btn.set_collapsed(True)

        def animate():
            nonlocal current_width
            if self._menu_collapsed: # We are expanding
                if current_width < target_width:
                    current_width += step
                    if current_width > target_width: current_width = target_width
                    self.menu.config(width=current_width)
                    self.after(delay, animate)
                else:
                    # Finished expanding
                    self._menu_collapsed = False
                    self.brand_title.place(x=50, y=10)
                    self.brand_sub.place(x=50, y=30)
                    for header_lbl in self.section_headers:
                        header_lbl.pack(fill="x", pady=(10, 2))
                    for btn in self.nav_buttons.values():
                        btn.set_collapsed(False)
            else: # We are collapsing
                if current_width > target_width:
                    current_width -= step
                    if current_width < target_width: current_width = target_width
                    self.menu.config(width=current_width)
                    self.after(delay, animate)
                else:
                    # Finished collapsing
                    self._menu_collapsed = True
                    # Texts already hidden

        animate()

    def _toggle_maximize(self):
        self.maximized = not self.maximized
        try:
            if self.maximized:
                self.state('zoomed')
            else:
                self.state('normal')
        except Exception:
            try:
                if self.maximized:
                    w = self.winfo_screenwidth()
                    h = self.winfo_screenheight()
                    self.geometry(f"{w}x{h}+0+0")
                else:
                    self.geometry("900x600")
            except Exception:
                pass

    def _restore(self):
        self.maximized = False
        try:
            self.state('normal')
        except Exception:
            try:
                self.geometry("900x600")
            except Exception:
                pass

    def _exit_fullscreen(self):
        self.fullscreen = False
        try:
            self.attributes("-fullscreen", False)
        except Exception:
            try:
                self.state('normal')
            except Exception:
                pass


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
