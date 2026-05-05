import tkinter as tk
from tkinter import messagebox, ttk
import random
import time
import os
import csv
from datetime import datetime

# ===== НАСТРОЙКИ =====
TICKETS_DIR = "tickets"  # папка с билетами
WAIT_TIME_MS = 3500
START_DELAY = 80
END_DELAY = 350


def load_tickets_from_dir(directory):
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
    def __init__(self, root):
        self.root = root
        self.root.title("Экзаменационные билеты")
        self.root.geometry("700x800")

        self.tickets_by_subject = load_tickets_from_dir(TICKETS_DIR)
        self.selected_subject = tk.StringVar()

        # ===== Выбор дисциплины =====
        self.subject_combo = ttk.Combobox(
            root,
            textvariable=self.selected_subject,
            values=list(self.tickets_by_subject.keys()),
            state="readonly",
            font=("Arial", 12)
        )
        self.subject_combo.pack(pady=10)
        if self.tickets_by_subject:
            self.subject_combo.current(0)

        self.entry_frame = tk.Frame(root)
        self.entry_frame.pack(pady=10)

        self.entry_label = ttk.Label(
            self.entry_frame,
            text="Студент: ",
            font=("Arial", 12)
        )
        self.entry_label.pack(side="left", padx=(0, 8))

        self.entry = ttk.Entry(
            self.entry_frame,
            width=42
        )
        self.entry.pack(side="left")

        self.button = tk.Button(
            root,
            text="🎟 Выдать билет",
            font=("Arial", 14),
            command=self.start_animation
        )
        self.button.pack(pady=10)

        self.text = tk.Text(
            root,
            wrap="word",
            font=("Arial", 13),
            state="disabled"
        )
        self.text.pack(expand=True, fill="both", padx=10, pady=10)

        self.start_time = None
        self.current_delay = START_DELAY

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
        
        self.text.tag_configure('bold', font=('Arial', 13, 'bold'))

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
        ticket = random.choice(self.tickets)

        self.save_student_ticket(ticket[0])

        self.text.tag_configure('bold', font=('Arial', 13, 'bold'))

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

    def save_student_ticket(self, ticket_name):
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


if __name__ == "__main__":
    root = tk.Tk()
    app = TicketApp(root)
    root.mainloop()
