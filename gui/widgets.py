#widgets perzonalizados
import tkinter as tk

# clase reutilizable para los placeholders de las barras de busqueda "luis estuvo aqui"
class EntryWithPlaceholder(tk.Entry):
    """Entry con texto placeholder personalizado"""
    
    def __init__(self, master=None, placeholder="", color="grey", **kwargs):
        super().__init__(master, **kwargs)
        
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self["fg"]
        
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        
        self._show_placeholder()
    
    def _show_placeholder(self):
        """Muestra el texto placeholder"""
        self.insert(0, self.placeholder)
        self.config(fg=self.placeholder_color)
    
    def _on_focus_in(self, event):
        """Elimina el placeholder al obtener foco"""
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.config(fg=self.default_fg_color)
    
    def _on_focus_out(self, event):
        """Vuelve a mostrar el placeholder si está vacío"""
        if not self.get():
            self._show_placeholder()
    
    def get_text(self):
        """Obtiene el texto real (sin placeholder)"""
        text = self.get()
        return "" if text == self.placeholder else text
    
    def clear(self):
        """Limpia el campo y muestra placeholder si está vacío"""
        self.delete(0, tk.END)
        self._show_placeholder()
    
    def set_text(self, text):
        """Establece texto en el campo"""
        self.delete(0, tk.END)
        if text:
            self.insert(0, text)
            self.config(fg=self.default_fg_color)
        else:
            self._show_placeholder()