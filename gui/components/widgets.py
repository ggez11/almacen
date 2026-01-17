# widgets personalizados
import tkinter as tk
from typing import Optional, Any, Dict

# clase reutilizable para los placeholders de las barras de busqueda "luis estuvo aqui"
class EntryWithPlaceholder(tk.Entry):
    """Entry con texto placeholder personalizado"""
    
    def __init__(
        self, 
        master: Optional[tk.Widget] = None, 
        placeholder: str = "", 
        color: str = "grey", 
        **kwargs: Any
    ) -> None:
        super().__init__(master, **kwargs)
        
        self.placeholder: str = placeholder
        self.placeholder_color: str = color
        # Guardamos el color de texto original para restaurarlo
        self.default_fg_color: str = self["fg"]
        
        # Tipamos los eventos de los binds
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        
        self._show_placeholder()
    
    def _show_placeholder(self) -> None:
        """Muestra el texto placeholder"""
        self.insert(0, self.placeholder)
        self.config(fg=self.placeholder_color)
    
    def _on_focus_in(self, event: tk.Event) -> None:
        """Elimina el placeholder al obtener foco"""
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.config(fg=self.default_fg_color)
    
    def _on_focus_out(self, event: tk.Event) -> None:
        """Vuelve a mostrar el placeholder si está vacío"""
        if not self.get():
            self._show_placeholder()
    
    def get_text(self) -> str:
        """Obtiene el texto real (sin el placeholder)"""
        text: str = self.get()
        return "" if text == self.placeholder else text
    
    def clear(self) -> None:
        """Limpia el campo y muestra placeholder"""
        self.delete(0, tk.END)
        self._show_placeholder()
    
    def set_text(self, text: str) -> None:
        """Establece texto en el campo de forma segura"""
        self.delete(0, tk.END)
        if text:
            self.insert(0, text)
            self.config(fg=self.default_fg_color)
        else:
            self._show_placeholder()