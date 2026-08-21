import tkinter as tk

class NavigationFrame(tk.Frame):
    """
    Modern Container that manages multiple page frames with a full
    History Stack (Back / Forward navigation) and lifecycle callbacks.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.pages = {}
        self.history = []
        self.forward_stack = []
        self.current_page = None
        self._listeners = []

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def add_page(self, name, page_class):
        frame = page_class(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_remove()
        self.pages[name] = frame

    def register_listener(self, callback):
        """Registers a callback function fn(current_page_name, can_back, can_forward)"""
        self._listeners.append(callback)

    def _notify_listeners(self):
        for cb in self._listeners:
            try:
                cb(self.current_page, self.can_go_back(), self.can_go_forward())
            except Exception:
                pass

    def can_go_back(self) -> bool:
        return len(self.history) > 0

    def can_go_forward(self) -> bool:
        return len(self.forward_stack) > 0

    def go_back(self):
        if not self.history:
            return
        prev = self.history.pop()
        if self.current_page:
            self.forward_stack.append(self.current_page)
        self._show_internal(prev)

    def go_forward(self):
        if not self.forward_stack:
            return
        nxt = self.forward_stack.pop()
        if self.current_page:
            self.history.append(self.current_page)
        self._show_internal(nxt)

    def show(self, name, record_history=True):
        if record_history and self.current_page and self.current_page != name:
            self.history.append(self.current_page)
            self.forward_stack.clear()
        self._show_internal(name)

    def _show_internal(self, name):
        self.current_page = name
        for n, p in self.pages.items():
            if n == name:
                p.grid()
                # Call lifecycle hooks if implemented by the page
                if hasattr(p, 'on_show') and callable(p.on_show):
                    try:
                        p.on_show()
                    except Exception:
                        pass
                elif hasattr(p, 'refresh_construct_data') and callable(p.refresh_construct_data):
                    try:
                        p.refresh_construct_data()
                    except Exception:
                        pass
                elif hasattr(p, 'refresh_data') and callable(p.refresh_data):
                    try:
                        p.refresh_data()
                    except Exception:
                        pass
            else:
                p.grid_remove()
        self._notify_listeners()
