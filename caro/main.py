# -*- coding: utf-8 -*-
import tkinter as tk

from gui import CaroGUI


def main() -> None:
    root = tk.Tk()
    CaroGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
