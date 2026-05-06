import csv
import random
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

"""Приложение для выдачи экзаменационных билетов.

Каждый файл в папке `tickets/` должен содержать первую строку с названием дисциплины,
а билеты внутри файла разделяются строками, начинающимися с `===`.
Можно использовать `*` в начале строки для выделения вопроса жирным шрифтом.
Результат выдачи сохраняется в `ticket_log.csv`.
"""

TICKETS_DIR = Path("tickets")
LOG_FILE = Path("ticket_log.csv")
WAIT_TIME_MS = 3500
START_DELAY = 80
END_DELAY = 350
LOG_FIELDS = ["Студент", "Дисциплина", "Билет", "Дата выдачи", "Время выдачи"]
TREE_COLUMNS = LOG_FIELDS


def load_tickets_from_dir(directory: Path) -> dict:
    """Загружает билеты из текстовых файлов указанной директории."""
    tickets_by_subject = {}
    if not directory.exists():
        messagebox.showerror("Ошибка", f"Директория {directory} не найдена")
        return tickets_by_subject

    for path in sorted(directory.glob("*.txt")):
        try:
            subject, tickets = parse_ticket_file(path)
            if subject:
                tickets_by_subject.setdefault(subject, []).extend(tickets)
        except Exception as error:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл {path.name}\n{error}")
    return tickets_by_subject


def parse_ticket_file(path: Path) -> tuple[str, list[list[str]]]:
    with path.open("r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]

    if not lines:
        return "", []

    subject = lines[0]
    tickets = []
    current_ticket = []

    for line in lines[1:]:
        if line.startswith("==="):
            if current_ticket:
                tickets.append(current_ticket)
            current_ticket = [line[3:].strip()]
        else:
            current_ticket.append(line)

    if current_ticket:
        tickets.append(current_ticket)

    return subject, tickets


def format_ticket_lines(ticket: list[str]) -> list[tuple[str, bool]]:
    formatted = []
    counter = 1
    for question in ticket[1:]:
        if question.startswith("*"):
            formatted.append((f"◪ {question[2:]}", True))
            counter = 1
        else:
            formatted.append((f"{counter}. {question}", False))
            counter += 1
    return formatted


class TicketApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Экзаменационные билеты")
        self.root.geometry("600x700")
        self.root.resizable(True, True)

        self.tickets_by_subject = load_tickets_from_dir(TICKETS_DIR)
        self.selected_subject = tk.StringVar()
        self.tickets: list[list[str]] = []
        self.tree: ttk.Treeview | None = None
        self.issued_window: tk.Toplevel | None = None
        self.start_time = 0.0
        self.current_delay = START_DELAY

        self._build_ui()

    def _build_ui(self):
        self._create_header()
        self._create_selection_area()
        self._create_buttons()
        self._create_display_area()

    def _create_header(self):
        header = tk.Frame(self.root, bg="#f0f0f0", height=40)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="🎓 Экзаменационные билеты",
            font=("Arial", 14, "bold"),
            bg="#f0f0f0",
            fg="#333"
        ).pack(expand=True)

    def _create_selection_area(self):
        frame = tk.Frame(self.root, padx=15, pady=10)
        frame.pack(fill="x")

        tk.Label(frame, text="Дисциплина:", font=("Arial", 11)).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        self.subject_combo = ttk.Combobox(
            frame,
            textvariable=self.selected_subject,
            values=list(self.tickets_by_subject),
            state="readonly",
            font=("Arial", 11),
            width=35
        )
        self.subject_combo.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        tk.Label(frame, text="Студент:", font=("Arial", 11)).grid(
            row=2, column=0, sticky="w", pady=(0, 5)
        )
        self.entry = ttk.Entry(frame, font=("Arial", 11), width=37)
        self.entry.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        frame.columnconfigure(0, weight=1)

    def _create_buttons(self):
        frame = tk.Frame(self.root, pady=5)
        frame.pack()

        self.button = tk.Button(
            frame,
            text="🎟 Выдать билет",
            font=("Arial", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=12,
            pady=6,
            command=self.start_animation
        )
        self.button.pack(side="left", padx=(0, 10))

        self.view_button = tk.Button(
            frame,
            text="📋 Выданные билеты",
            font=("Arial", 11, "bold"),
            bg="#2196F3",
            fg="white",
            padx=12,
            pady=6,
            command=self.show_issued_tickets
        )
        self.view_button.pack(side="left")

    def _create_display_area(self):
        frame = tk.Frame(self.root, padx=15, pady=5)
        frame.pack(fill="both", expand=True)

        self.text = tk.Text(
            frame,
            wrap="word",
            font=("Arial", 10),
            state="disabled",
            padx=5,
            pady=5
        )
        self.text.pack(fill="both", expand=True)

    def start_animation(self):
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
        elapsed = (time.time() - self.start_time) * 1000
        if elapsed >= WAIT_TIME_MS:
            self.show_ticket()
            return

        ticket_name = random.choice(self.tickets)[0]
        self._show_text(
            ["🎰 Выбор экзаменационного билета", "", f"▶ {ticket_name}", "", "Пожалуйста, ожидайте..."],
            bold_indices={2}
        )

        progress = elapsed / WAIT_TIME_MS
        self.current_delay = int(START_DELAY + (END_DELAY - START_DELAY) * progress)
        self.root.after(self.current_delay, self.animate)

    def show_ticket(self):
        ticket = random.choice(self.tickets)
        self.save_student_ticket(ticket[0])

        ticket_lines = format_ticket_lines(ticket)
        lines = [f"🎟 {ticket[0]}", ""]
        lines.extend(text for text, _ in ticket_lines)

        bold_indices = {0} | {index + 2 for index, (_, bold) in enumerate(ticket_lines) if bold}
        self._show_text(lines, bold_indices=bold_indices)

        self.button.config(state="normal")
        if self.issued_window and self.issued_window.winfo_exists():
            self.update_issued_window()

    def _show_text(self, lines: list[str], bold_indices: set[int] = None):
        bold_indices = bold_indices or set()
        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.tag_configure("bold", font=("Arial", 10, "bold"))

        for index, line in enumerate(lines):
            self.text.insert(tk.END, line + "\n", "bold" if index in bold_indices else None)
        self.text.config(state="disabled")

    def save_student_ticket(self, ticket_name: str):
        entry_value = self.entry.get()
        combo_value = self.selected_subject.get()
        now = datetime.now()
        data = {
            "Студент": entry_value,
            "Дисциплина": combo_value,
            "Билет": ticket_name,
            "Дата выдачи": now.strftime("%d.%m.%Y"),
            "Время выдачи": now.strftime("%H:%M"),
        }

        try:
            file_exists = LOG_FILE.exists() and LOG_FILE.stat().st_size > 0
            with LOG_FILE.open("a", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=LOG_FIELDS)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(data)
        except Exception as error:
            messagebox.showerror("Ошибка", f"Не удалось записать файл логов\n{error}")

    def show_issued_tickets(self):
        if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
            messagebox.showinfo("Информация", "Лог выданных билетов пуст.")
            return

        if self.issued_window and self.issued_window.winfo_exists():
            self.issued_window.lift()
            self.update_issued_window()
            return

        self.issued_window = tk.Toplevel(self.root)
        self.issued_window.title("Выданные билеты")
        self.issued_window.geometry("800x600")

        frame = tk.Frame(self.issued_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(frame, columns=TREE_COLUMNS, show="headings", height=20)
        for col in TREE_COLUMNS:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        self.update_issued_window()

    def update_issued_window(self):
        if not self.tree:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            with LOG_FILE.open("r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.tree.insert("", "end", values=[row[field] for field in LOG_FIELDS])
        except Exception as error:
            messagebox.showerror("Ошибка", f"Не удалось прочитать лог файл\n{error}")


if __name__ == "__main__":
    root = tk.Tk()
    TicketApp(root)
    root.mainloop()
