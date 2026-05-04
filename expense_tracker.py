import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

DATE_FMT = "%Y-%m-%d"
DEFAULT_FILE = "expenses.json"
CATEGORIES = ["Еда", "Транспорт", "Развлечения", "Покупки", "Здоровье", "Другое"]


class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("1100x680")
        self.root.minsize(980, 620)

        self.expenses = []
        self.filtered_expenses = []

        self.amount_var = tk.StringVar()
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.date_var = tk.StringVar(value=datetime.now().strftime(DATE_FMT))
        self.filter_category_var = tk.StringVar(value="Все")
        self.filter_date_from_var = tk.StringVar()
        self.filter_date_to_var = tk.StringVar()
        self.period_from_var = tk.StringVar()
        self.period_to_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Готово к работе")
        self.total_var = tk.StringVar(value="Сумма за период: 0.00")

        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        entry_frame = ttk.LabelFrame(main, text="Добавление расхода", padding=12)
        entry_frame.grid(row=0, column=0, sticky="ew")
        for i in range(7):
            entry_frame.columnconfigure(i, weight=1)

        ttk.Label(entry_frame, text="Сумма").grid(row=0, column=0, sticky="w")
        ttk.Entry(entry_frame, textvariable=self.amount_var).grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(entry_frame, text="Категория").grid(row=0, column=1, sticky="w")
        ttk.Combobox(entry_frame, textvariable=self.category_var, values=CATEGORIES, state="readonly").grid(row=1, column=1, sticky="ew", padx=(0, 8))

        ttk.Label(entry_frame, text="Дата (ГГГГ-ММ-ДД)").grid(row=0, column=2, sticky="w")
        ttk.Entry(entry_frame, textvariable=self.date_var).grid(row=1, column=2, sticky="ew", padx=(0, 8))

        ttk.Button(entry_frame, text="Добавить расход", command=self.add_expense).grid(row=1, column=3, sticky="ew", padx=(0, 8))
        ttk.Button(entry_frame, text="Сохранить JSON", command=self.save_json).grid(row=1, column=4, sticky="ew", padx=(0, 8))
        ttk.Button(entry_frame, text="Загрузить JSON", command=self.load_json).grid(row=1, column=5, sticky="ew", padx=(0, 8))
        ttk.Button(entry_frame, text="Удалить выбранное", command=self.delete_selected).grid(row=1, column=6, sticky="ew")

        filter_frame = ttk.LabelFrame(main, text="Фильтрация и подсчёт", padding=12)
        filter_frame.grid(row=1, column=0, sticky="ew", pady=12)
        for i in range(10):
            filter_frame.columnconfigure(i, weight=1)

        ttk.Label(filter_frame, text="Категория").grid(row=0, column=0, sticky="w")
        filter_values = ["Все"] + CATEGORIES
        ttk.Combobox(filter_frame, textvariable=self.filter_category_var, values=filter_values, state="readonly").grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(filter_frame, text="Дата от").grid(row=0, column=1, sticky="w")
        ttk.Entry(filter_frame, textvariable=self.filter_date_from_var).grid(row=1, column=1, sticky="ew", padx=(0, 8))

        ttk.Label(filter_frame, text="Дата до").grid(row=0, column=2, sticky="w")
        ttk.Entry(filter_frame, textvariable=self.filter_date_to_var).grid(row=1, column=2, sticky="ew", padx=(0, 8))

        ttk.Button(filter_frame, text="Применить фильтр", command=self.apply_filters).grid(row=1, column=3, sticky="ew", padx=(0, 8))
        ttk.Button(filter_frame, text="Сбросить фильтр", command=self.reset_filters).grid(row=1, column=4, sticky="ew", padx=(0, 16))

        ttk.Label(filter_frame, text="Период от").grid(row=0, column=5, sticky="w")
        ttk.Entry(filter_frame, textvariable=self.period_from_var).grid(row=1, column=5, sticky="ew", padx=(0, 8))

        ttk.Label(filter_frame, text="Период до").grid(row=0, column=6, sticky="w")
        ttk.Entry(filter_frame, textvariable=self.period_to_var).grid(row=1, column=6, sticky="ew", padx=(0, 8))

        ttk.Button(filter_frame, text="Подсчитать сумму", command=self.calculate_total).grid(row=1, column=7, sticky="ew", padx=(0, 8))
        ttk.Label(filter_frame, textvariable=self.total_var, font=("Arial", 11, "bold")).grid(row=1, column=8, columnspan=2, sticky="w")

        table_frame = ttk.LabelFrame(main, text="Список расходов", padding=12)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("id", "amount", "category", "date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)
        self.tree.heading("id", text="ID")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("category", text="Категория")
        self.tree.heading("date", text="Дата")
        self.tree.column("id", width=70, anchor="center")
        self.tree.column("amount", width=140, anchor="e")
        self.tree.column("category", width=220, anchor="center")
        self.tree.column("date", width=160, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        status = ttk.Label(main, textvariable=self.status_var, relief="sunken", anchor="w", padding=6)
        status.grid(row=3, column=0, sticky="ew", pady=(12, 0))

    def _validate_positive_amount(self, amount_text):
        try:
            amount = float(amount_text.replace(",", "."))
        except ValueError:
            raise ValueError("Сумма должна быть числом.")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительным числом.")
        return round(amount, 2)

    def _validate_date(self, date_text, empty_allowed=False):
        date_text = date_text.strip()
        if empty_allowed and not date_text:
            return None
        try:
            return datetime.strptime(date_text, DATE_FMT).date()
        except ValueError:
            raise ValueError("Дата должна быть в формате ГГГГ-ММ-ДД.")

    def add_expense(self):
        try:
            amount = self._validate_positive_amount(self.amount_var.get())
            date_obj = self._validate_date(self.date_var.get())
            category = self.category_var.get().strip() or "Другое"
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
            return

        item = {
            "id": len(self.expenses) + 1,
            "amount": amount,
            "category": category,
            "date": date_obj.strftime(DATE_FMT),
        }
        self.expenses.append(item)
        self.refresh_table(self.expenses)
        self.amount_var.set("")
        self.status_var.set(f"Добавлен расход: {amount:.2f} | {category} | {item['date']}")

    def refresh_table(self, data=None):
        self.tree.delete(*self.tree.get_children())
        data = self.expenses if data is None else data
        self.filtered_expenses = list(data)
        for item in data:
            self.tree.insert("", "end", values=(item["id"], f"{item['amount']:.2f}", item["category"], item["date"]))

    def apply_filters(self):
        try:
            category = self.filter_category_var.get()
            date_from = self._validate_date(self.filter_date_from_var.get(), empty_allowed=True)
            date_to = self._validate_date(self.filter_date_to_var.get(), empty_allowed=True)
            if date_from and date_to and date_from > date_to:
                raise ValueError("Дата 'от' не может быть больше даты 'до'.")
        except ValueError as e:
            messagebox.showerror("Ошибка фильтра", str(e))
            return

        filtered = []
        for item in self.expenses:
            item_date = datetime.strptime(item["date"], DATE_FMT).date()
            if category != "Все" and item["category"] != category:
                continue
            if date_from and item_date < date_from:
                continue
            if date_to and item_date > date_to:
                continue
            filtered.append(item)

        self.refresh_table(filtered)
        self.status_var.set(f"Фильтр применён. Найдено записей: {len(filtered)}")

    def reset_filters(self):
        self.filter_category_var.set("Все")
        self.filter_date_from_var.set("")
        self.filter_date_to_var.set("")
        self.refresh_table(self.expenses)
        self.status_var.set("Фильтры сброшены")

    def calculate_total(self):
        try:
            date_from = self._validate_date(self.period_from_var.get(), empty_allowed=True)
            date_to = self._validate_date(self.period_to_var.get(), empty_allowed=True)
            if date_from and date_to and date_from > date_to:
                raise ValueError("Период 'от' не может быть позже периода 'до'.")
        except ValueError as e:
            messagebox.showerror("Ошибка периода", str(e))
            return

        total = 0.0
        for item in self.expenses:
            item_date = datetime.strptime(item["date"], DATE_FMT).date()
            if date_from and item_date < date_from:
                continue
            if date_to and item_date > date_to:
                continue
            total += item["amount"]

        self.total_var.set(f"Сумма за период: {total:.2f}")
        self.status_var.set("Подсчёт суммы выполнен")

    def save_json(self):
        file_path = filedialog.asksaveasfilename(
            title="Сохранить JSON",
            defaultextension=".json",
            initialfile=DEFAULT_FILE,
            filetypes=[("JSON files", "*.json")],
        )
        if not file_path:
            return
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.expenses, f, ensure_ascii=False, indent=4)
        self.status_var.set(f"Данные сохранены: {os.path.basename(file_path)}")
        messagebox.showinfo("Сохранение", "Данные успешно сохранены в JSON.")

    def load_json(self):
        file_path = filedialog.askopenfilename(
            title="Загрузить JSON",
            filetypes=[("JSON files", "*.json")],
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            validated = []
            for idx, item in enumerate(data, start=1):
                amount = self._validate_positive_amount(str(item.get("amount", "")))
                date_obj = self._validate_date(str(item.get("date", "")))
                category = str(item.get("category", "Другое")).strip() or "Другое"
                validated.append({
                    "id": idx,
                    "amount": amount,
                    "category": category,
                    "date": date_obj.strftime(DATE_FMT),
                })
            self.expenses = validated
            self.refresh_table(self.expenses)
            self.status_var.set(f"Загружено записей: {len(self.expenses)}")
            messagebox.showinfo("Загрузка", "Данные успешно загружены из JSON.")
        except (json.JSONDecodeError, OSError, ValueError) as e:
            messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить файл: {e}")

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Удаление", "Сначала выберите запись в таблице.")
            return

        selected_values = self.tree.item(selected[0], "values")
        selected_id = int(selected_values[0])
        self.expenses = [item for item in self.expenses if item["id"] != selected_id]
        for idx, item in enumerate(self.expenses, start=1):
            item["id"] = idx
        self.refresh_table(self.expenses)
        self.status_var.set(f"Удалена запись ID {selected_id}")


def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default="")
    except Exception:
        pass
    app = ExpenseTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
