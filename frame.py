import logging
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
import lxml.etree as ET
from main import DistributedDian


MAX_PATH_LENGTH = 40
BTN_WIDTH = 210


class FileSelectionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Выбор файлов и папки")
        self.geometry("450x400")
        ctk.set_appearance_mode("dark")

        self.distributed_dian = None

        # Переменные для хранения путей
        self.file1_label = tk.StringVar(value="Файл не выбран")
        self.file2_label = tk.StringVar(value="Файл не выбран")
        self.file1_path = None
        self.file2_path = None

        # Фрейм для выбора файлов
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=20, padx=20, fill="both", expand=True)

        ctk.CTkLabel(self.frame, text="Распределение заплывов",
                     font=("Arial", 14)).pack(pady=5)

        # Первый файл
        self.label_file1 = ctk.CTkLabel(
            self.frame,
            textvariable=self.file1_label,
            wraplength=400
        )
        self.label_file1.pack(pady=(5, 2))
        self.btn_file1 = ctk.CTkButton(
            self.frame,
            text="Выбрать Swimming-файл",
            width=BTN_WIDTH,
            command=self.select_file1
        )
        self.btn_file1.pack(pady=5)

        # Второй файл
        self.label_file2 = ctk.CTkLabel(
            self.frame,
            textvariable=self.file2_label,
            wraplength=400
        )
        self.label_file2.pack(pady=(10, 2))
        self.btn_file2 = ctk.CTkButton(
            self.frame,
            text="Выбрать Lenex-файл",
            width=BTN_WIDTH,
            command=self.select_file2
        )
        self.btn_file2.pack(pady=5)

        self.btn_start = ctk.CTkButton(
            self.frame,
            text="Распределить",
            width=BTN_WIDTH,
            command=self.start_process,
            state='disabled'
        )
        self.btn_start.pack(pady=20)

        self.btn_save_file = ctk.CTkButton(
            self.frame,
            text="Скачать",
            width=BTN_WIDTH,
            command=self.save_file
        )
        self.btn_save_file.pack(pady=5)

    def truncate_path(self, path):
        if len(path) > MAX_PATH_LENGTH:
            return f"...{os.sep}{os.path.basename(path)}"
        return path

    def update_start_state(self):
        state = 'normal' if (
            self.file1_path
            and self.file2_path
        ) else 'disabled'

        self.btn_start.configure(
            state=state
        )
        self.btn_save_file.configure(
            state=state
        )

    def select_file1(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл",
            filetypes=[('Swimming Файл', '*.swimming')]
        )
        if file_path:
            self.file1_path = file_path
            self.file1_label.set(self.truncate_path(file_path))
        self.update_start_state()

    def select_file2(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл",
            filetypes=[('Lenex файл', ('*.lxf', '.lef'))]
        )
        if file_path:
            self.file2_path = file_path
            self.file2_label.set(self.truncate_path(file_path))
        self.update_start_state()

    def start_process(self):
        self.distributed_dian = DistributedDian(
            self.file2_path, self.file1_path)
        self.distributed_dian.parse()

    def save_file(self):
        file_path = filedialog.asksaveasfilename(
            title="Выберите файл",
            filetypes=[('Swimming файл', ('*.swimming'))],
            defaultextension='*.swimming'
        )
        if not file_path:
            return

        element = self.distributed_dian.dian.dump('MEET')
        xml = ET.tostring(element, encoding="utf-8", xml_declaration=True)
        with open(file_path, 'wb+') as file:
            file.write(xml)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = FileSelectionApp()
    app.mainloop()
