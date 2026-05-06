import tkinter as tk
from tkinter import messagebox, ttk
import random
import time
import os
import csv
from datetime import datetime

"""Приложение для выдачи экзаменационных билетов.

Каждый файл в папке `tickets/` должен содержать первую строку с названием дисциплины,
а билеты внутри файла разделяются строками, начинающимися с `===`. также можно использовать `*` в начале строки для выделения вопросов жирным шрифтом.
Результат выдачи сохраняется в `ticket_log.csv`.
"""

# ===== НАСТРОЙКИ =====
TICKETS_DIR = "tickets"  # папка с билетами
WAIT_TIME_MS = 3500
START_DELAY = 80
END_DELAY = 350


def load_tickets_from_dir(directory):
    """Загружает билеты из текстовых файлов указанной директории.

    Ожидает, что каждый файл содержит:
    - первую строку с названием дисциплины
    - разделитель билетов "==="
    - строки с вопросами или содержимым билета

    Возвращает словарь, где ключ — дисциплина, а значение — список билетов.
    """

    tickets_by_subject = {}

    if not os.path.exists(directory):
        messagebox.showerror("Ошибка", f"Директория {directory} не найдена")
        return tickets_by_subject

    for filename in os.listdir(directory):
        if not filename.lower().endswith(".txt"):
            continue
        path = os.path.join(directory, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
                if not lines:
                    continue

                subject = lines[0]  # первая строка файла — название дисциплины
                current_ticket = []
                tickets = []

                for line in lines[1:]:
                    if line.startswith("==="):
                        if current_ticket:
                            tickets.append(current_ticket)
                        current_ticket = [line.replace("===", "").strip()]
                    else:
                        current_ticket.append(line)

                if current_ticket:
                    tickets.append(current_ticket)

                if subject not in tickets_by_subject:
                    tickets_by_subject[subject] = []

                tickets_by_subject[subject].extend(tickets)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл {filename}\n{e}")

    return tickets_by_subject



class TicketApp:
    """GUI-приложение для выбора дисциплины и выдачи случайных экзаменационных билетов."""

    def __init__(self, root):
        self.root = root
        self.root.title("Экзаменационные билеты")
        self.root.geometry("600x700")
        self.root.resizable(True, True)

        self.tickets_by_subject = load_tickets_from_dir(TICKETS_DIR)
        self.selected_subject = tk.StringVar()

        # Создаем фреймы для организации компоновки
        self.header_frame = tk.Frame(root, bg="#f0f0f0", height=40)
        self.header_frame.pack(fill="x", side="top")
        self.header_frame.pack_propagate(False)

        self.selection_frame = tk.Frame(root, padx=15, pady=10)
        self.selection_frame.pack(fill="x")

        self.button_frame = tk.Frame(root, pady=5)
        self.button_frame.pack()

        self.display_frame = tk.Frame(root, padx=15, pady=5)
        self.display_frame.pack(fill="both", expand=True)

        # Заголовок
        self.title_label = tk.Label(
            self.header_frame,
            text="🎓 Экзаменационные билеты",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0",
            fg="#333"
        )
        self.title_label.pack(expand=True)

        # Выбор дисциплины
        self.subject_label = tk.Label(
            self.selection_frame,
            text="Дисциплина:",
            font=("Arial", 11)
        )
        self.subject_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.subject_combo = ttk.Combobox(
            self.selection_frame,
            textvariable=self.selected_subject,
            values=list(self.tickets_by_subject.keys()),
            state="readonly",
            font=("Arial", 11),
            width=35
        )
        self.subject_combo.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Ввод имени студента
        self.student_label = tk.Label(
            self.selection_frame,
            text="Студент:",
            font=("Arial", 11)
        )
        self.student_label.grid(row=2, column=0, sticky="w", pady=(0, 5))

        self.entry = ttk.Entry(
            self.selection_frame,
            font=("Arial", 11),
            width=37
        )
        self.entry.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        # Кнопка выдачи билета
        self.button = tk.Button(
            self.button_frame,
            text="🎟 Выдать билет",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=15,
            pady=8,
            command=self.start_animation
        )
        self.button.pack(side="left", padx=(0, 10))

        # Кнопка просмотра выданных билетов
        self.view_button = tk.Button(
            self.button_frame,
            text="📋 Выданные билеты",
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            padx=15,
            pady=8,
            command=self.show_issued_tickets
        )
        self.view_button.pack(side="left")

        # Область отображения билета
        self.text = tk.Text(
            self.display_frame,
            wrap="word",
            font=("Arial", 11),
            state="disabled",
            padx=5,
            pady=5
        )
        self.text.pack(fill="both", expand=True)

        # Настраиваем grid для selection_frame
        self.selection_frame.columnconfigure(0, weight=1)

        self.start_time = None
        self.current_delay = START_DELAY

        if self.tickets_by_subject:
            self.subject_combo.current(0)

    def start_animation(self):
        """Запускает анимацию выбора билета и блокирует кнопку до окончания процесса."""
        subject = self.selected_subject.get()
        if not subject or subject not in self.tickets_by_subject:
            messagebox.showwarning("Внимание", "Выберите дисциплину")
            return

        self.tickets = self.tickets_by_subject[subject]
        self.button.config(state="disabled")
        self.start_time = time.time()
        self.current_delay = START_DELAY
        self.animate()

    def animate(self):
        """Выполняет визуальную имитацию выбора билета с прогрессом времени."""
        elapsed = (time.time() - self.start_time) * 1000

        if elapsed >= WAIT_TIME_MS:
            self.show_ticket()
            return

        ticket_name = random.choice(self.tickets)[0]
        
        self.text.tag_configure('bold', font=('Arial', 11, 'bold'))

        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, "🎰 Выбор экзаменационного билета\n\n")
        self.text.insert(tk.END, f"▶ {ticket_name}\n\n", 'bold')
        self.text.insert(tk.END, "Пожалуйста, ожидайте...")
        self.text.config(state="disabled")

        progress = elapsed / WAIT_TIME_MS
        self.current_delay = int(START_DELAY + (END_DELAY - START_DELAY) * progress)
        self.root.after(self.current_delay, self.animate)

    def show_ticket(self):
        """Отображает выбранный билет и сохраняет запись о выдаче."""
        ticket = random.choice(self.tickets)

        self.save_student_ticket(ticket[0])

        self.text.tag_configure('bold', font=('Arial', 11, 'bold'))

        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, f"🎟 {ticket[0]}\n\n", 'bold')  # имя файла или можно показывать свой формат

        n = 1
        for i, question in enumerate(ticket[1:], start=1):
            if question.startswith("*"):
                self.text.insert(tk.END, f"◪ {question[2:]}\n\n", 'bold')
                n = 1
            else:
                self.text.insert(tk.END, f"{n}. {question}\n\n")
                n += 1

        self.text.config(state="disabled")
        self.button.config(state="normal")

        # Обновляем окно выданных билетов, если оно открыто
        if hasattr(self, 'issued_window') and self.issued_window.winfo_exists():
            self.update_issued_window()

    def save_student_ticket(self, ticket_name):
        """Сохраняет информацию о выданном билете в CSV-файл логов."""
        entry_value = self.entry.get()
        combo_value = self.selected_subject.get()
        now = datetime.now()
        issued_date = now.strftime("%d.%m.%Y")
        issued_time = now.strftime("%H:%M")
        log_path = os.path.join(os.getcwd(), "ticket_log.csv")
        file_exists = os.path.exists(log_path)

        try:
            with open(log_path, "a", encoding="utf-8", newline="") as f:
                fieldnames = ["Студент", "Дисциплина", "Билет", "Дата выдачи", "Время выдачи"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists or os.path.getsize(log_path) == 0:
                    writer.writeheader()
                writer.writerow({
                    "Студент": entry_value,
                    "Дисциплина": combo_value,
                    "Билет": ticket_name,
                    "Дата выдачи": issued_date,
                    "Время выдачи": issued_time,
                })
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось записать файл логов\n{e}")


    def show_issued_tickets(self):
        """Открывает окно с просмотром всех выданных билетов."""
        log_path = os.path.join(os.getcwd(), "ticket_log.csv")
        if not os.path.exists(log_path):
            messagebox.showinfo("Информация", "Лог выданных билетов пуст.")
            return

        # Проверяем, если окно уже открыто
        if hasattr(self, 'issued_window') and self.issued_window.winfo_exists():
            self.issued_window.lift()  # Поднимаем окно наверх
            self.update_issued_window()
            return

        # Создаем новое окно
        self.issued_window = tk.Toplevel(self.root)
        self.issued_window.title("Выданные билеты")
        self.issued_window.geometry("800x600")

        # Фрейм для Treeview
        frame = tk.Frame(self.issued_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Создаем Treeview
        columns = ("Студент", "Дисциплина", "Билет", "Дата выдачи", "Время выдачи")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)

        # Настраиваем колонки
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")

        # Добавляем скроллбар
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # Загружаем данные из CSV
        self.update_issued_window()


    def update_issued_window(self):
        """Обновляет таблицу выданных билетов."""
        if not hasattr(self, 'tree'):
            return

        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)

        log_path = os.path.join(os.getcwd(), "ticket_log.csv")
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.tree.insert("", "end", values=(row["Студент"], row["Дисциплина"], row["Билет"], row["Дата выдачи"], row["Время выдачи"]))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать лог файл\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TicketApp(root)
    root.mainloop()
