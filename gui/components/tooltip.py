import tkinter as tk
from typing import Optional

class ToolTip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget: tk.Widget = widget
        self.text: str = text
        self.tip_window: Optional[tk.Toplevel] = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event: Optional[tk.Event] = None) -> None:
        if self.tip_window or not self.text:
            return
        # Calcular posición
        x: int = self.widget.winfo_rootx() + 20
        y: int = self.widget.winfo_rooty() + 20
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True) # Sin bordes
        tw.wm_geometry(f"+{x}+{y}")
        
        label: tk.Label = tk.Label(
            tw, text=self.text, justify="left",
            background="#111827", foreground="white",
            relief="flat", borderwidth=1,
            font=("Segoe UI", 8), padx=8, pady=4
        )
        label.pack()

    def hide_tip(self, event: Optional[tk.Event] = None) -> None:
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None