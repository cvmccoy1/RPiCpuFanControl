#!/usr/bin/env python3

import tkinter as tk
import tkinter.ttk as ttk

class FormattedSpinbox(ttk.Spinbox):
    def __init__(self, master, **kwargs):
        kwargs['command'] = self.command
        super().__init__(master, **kwargs)
    def set(self, value):
        super().set(value)
        self.command()
    def get(self):
        value = super().get().strip().split()[0]
        return float(value)
    def command(self):
        value = self.get()
        self.delete(0, tk.END)
        self.insert(0, f'Set Point = {float(value):.0f} ℃')