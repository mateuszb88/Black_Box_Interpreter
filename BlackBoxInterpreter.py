import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator

# Ustawienie backendu dla matplotlib
matplotlib.use("TkAgg")

class BlackBoxInterpreter:
    def __init__(self, root):
        self.root = root
        self.root.title("Black Box Interpreter")
        
        # --- Struktury danych ---
        self.general_params = []
        self.event_data_names = []
        self.event_waveform_names = []
        
        # Słowniki danych
        self.event_data_values_map = {} 
        self.event_waveform_values_map = {} 
        
        # Stan widoku
        self.current_selected_event_index = None
        self.current_window_size = None 
        self.current_view_start = 0     
        self.max_data_length = 0        

        # Maksymalizacja okna
        try:
            self.root.state('zoomed')
        except tk.TclError:
            w, h = root.winfo_screenwidth(), root.winfo_screenheight()
            self.root.geometry(f"{w}x{h}+0+0")

        # --- Główny układ ---
        main_container = tk.Frame(root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # --- LEWA STRONA ---
        self.left_frame = tk.Frame(main_container, width=400, bg="#e0e0e0", padx=10, pady=10)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.left_frame.pack_propagate(False)

        # --- PRAWA STRONA ---
        self.right_frame = tk.Frame(main_container, bg="white")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Prawa Góra (Panel sterowania)
        self.right_top_frame = tk.Frame(self.right_frame, height=160, bg="#f9f9f9", padx=10, pady=10)
        self.right_top_frame.pack(side=tk.TOP, fill=tk.X)
        self.right_top_frame.pack_propagate(False)

        # Prawa Dół (Wykresy)
        self.right_bottom_frame = tk.Frame(self.right_frame, bg="white")
        self.right_bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # ================= ELEMENTY LEWEJ STRONY =================
        self.upload_btn = tk.Button(
            self.left_frame, 
            text="Załaduj plik",
            command=self.upload_file,
            height=2,
            width=25
        )
        self.upload_btn.pack(pady=(10, 20))

        lbl_params = tk.Label(self.left_frame, text="Wykryte parametry:", bg="#e0e0e0", font=("Arial", 10, "bold"))
        lbl_params.pack(anchor="w")

        self.params_text = tk.Text(self.left_frame, width=30, height=20, font=("Consolas", 9))
        self.params_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

        self.params_text.tag_config("header", foreground="blue", font=("Arial", 10, "bold"))
        self.params_text.tag_config("value", foreground="darkgreen", font=("Consolas", 9, "bold"))
        self.params_text.tag_config("info", foreground="gray", font=("Consolas", 8))
        self.params_text.tag_config("event_val", foreground="blue", font=("Consolas", 9, "bold"))

        params_scroll = tk.Scrollbar(self.left_frame, command=self.params_text.yview)
        params_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        self.params_text.config(yscrollcommand=params_scroll.set)

        # ================= ELEMENTY PRAWEJ STRONY (GÓRA - PANEL) =================
        
        # Wiersz 1: Sterowanie główne
        row1 = tk.Frame(self.right_top_frame, bg="#f9f9f9")
        row1.pack(side=tk.TOP, fill=tk.X, pady=5)

        # Numer zdarzenia (Spinbox)
        lbl_event_idx = tk.Label(row1, text="Numer zdarzenia:", bg="#f9f9f9", font=("Arial", 10))
        lbl_event_idx.pack(side=tk.LEFT, padx=(0, 5))

        self.entry_event_idx = tk.Spinbox(row1, from_=0, to=1000000, width=10)
        self.entry_event_idx.pack(side=tk.LEFT, padx=5)

        tk.Label(row1, text=" | ", bg="#f9f9f9", fg="gray").pack(side=tk.LEFT, padx=10)

        # Zakres próbek (Oś X) - Spinboxy
        lbl_range = tk.Label(row1, text="Zakres próbek (X):", bg="#f9f9f9", font=("Arial", 10))
        lbl_range.pack(side=tk.LEFT, padx=(0, 5))

        self.entry_sample_start = tk.Spinbox(row1, from_=0, to=1000000, width=6)
        self.entry_sample_start.pack(side=tk.LEFT, padx=2)

        tk.Label(row1, text="-", bg="#f9f9f9").pack(side=tk.LEFT)

        self.entry_sample_end = tk.Spinbox(row1, from_=0, to=1000000, width=6)
        self.entry_sample_end.pack(side=tk.LEFT, padx=2)

        tk.Label(row1, text=" | ", bg="#f9f9f9", fg="gray").pack(side=tk.LEFT, padx=10)

        # Przycisk Aktualizuj
        btn_update = tk.Button(row1, text="Aktualizuj", command=self.on_update_click)
        btn_update.pack(side=tk.LEFT, padx=5)

        # Przycisk Resetuj
        btn_reset = tk.Button(row1, text="Resetuj zakresy", command=self.reset_ranges)
        btn_reset.pack(side=tk.LEFT, padx=5)

        # Wiersz 2: Wybór przebiegów i zakresy Y
        row2 = tk.Frame(self.right_top_frame, bg="#f9f9f9")
        row2.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.combos = []
        self.y_min_entries = [] # Pola na min Y
        self.y_max_entries = [] # Pola na max Y

        for i in range(4):
            # Kontener kolumny dla pojedynczego przebiegu
            col_frame = tk.Frame(row2, bg="#f9f9f9")
            col_frame.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

            # Etykieta i Combobox
            lbl = tk.Label(col_frame, text=f"Przebieg {i+1}", bg="#f9f9f9", font=("Arial", 8, "bold"))
            lbl.pack(side=tk.TOP, anchor="w")

            cb = ttk.Combobox(col_frame, state="readonly", width=15)
            cb.pack(side=tk.TOP, fill=tk.X)
            self.combos.append(cb)

            # Panel zakresu Y pod Comboboxem
            y_frame = tk.Frame(col_frame, bg="#f9f9f9")
            y_frame.pack(side=tk.TOP, fill=tk.X, pady=2)

            tk.Label(y_frame, text="Y:", bg="#f9f9f9", font=("Arial", 8)).pack(side=tk.LEFT)
            
            # Spinbox dla Y Min (pozwalamy na ujemne)
            entry_min = tk.Spinbox(y_frame, from_=-100000, to=100000, increment=1, width=5)
            entry_min.pack(side=tk.LEFT, padx=2)
            
            tk.Label(y_frame, text="-", bg="#f9f9f9").pack(side=tk.LEFT)
            
            # Spinbox dla Y Max
            entry_max = tk.Spinbox(y_frame, from_=-100000, to=100000, increment=1, width=5)
            entry_max.pack(side=tk.LEFT, padx=2)

            self.y_min_entries.append(entry_min)
            self.y_max_entries.append(entry_max)

        # ================= ELEMENTY PRAWEJ STRONY (DÓŁ - WYKRESY) =================
        
        # Figura matplotlib
        self.fig = plt.Figure(figsize=(6, 8), dpi=100)
        self.axes = []
        for i in range(4):
            ax = self.fig.add_subplot(4, 1, i+1)
            ax.set_ylabel(f"Przebieg {i+1}")
            ax.grid(True)
            # Wymuszenie liczb całkowitych na osi X
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            self.axes.append(ax)

        self.fig.tight_layout()

        # Canvas (Wykres)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_bottom_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Pasek przewijania (Scrollbar) pod wykresem
        self.scroll_x = tk.Scrollbar(self.right_bottom_frame, orient="horizontal", command=self.on_scroll_change)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

    def upload_file(self):
        file_path = filedialog.askopenfilename(
            title="Wybierz plik CSV",
            filetypes=[("Pliki CSV", "*.csv"), ("Wszystkie pliki", "*.*")]
        )

        if file_path:
            self.process_file(file_path)

    def process_file(self, file_path):
        try:
            content = ""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='cp1250') as f:
                    content = f.read()

            self.current_selected_event_index = None
            self.entry_event_idx.delete(0, tk.END)
            self.entry_sample_start.delete(0, tk.END)
            self.entry_sample_end.delete(0, tk.END)
            
            # Reset comboboxów i pól Y
            for cb in self.combos:
                cb.set('')
                cb['values'] = []
            
            for e in self.y_min_entries:
                e.delete(0, tk.END)
            for e in self.y_max_entries:
                e.delete(0, tk.END)

            # --- AUTOMATYCZNA DETEKCJA SEPARATORA ---
            detected_delimiter = ';' # domyślny
            # Szukamy linii "Event Index" i sprawdzamy co jest po niej
            for line in content.splitlines():
                if line.startswith("Event Index"):
                    if ";" in line:
                        detected_delimiter = ';'
                    elif "," in line:
                        detected_delimiter = ','
                    break
            
            # Uruchomienie parsowania z wykrytym separatorem
            self.extract_parameters(content, detected_delimiter)

            for cb in self.combos:
                cb['values'] = self.event_waveform_names
            
            if self.event_waveform_names:
                for i, cb in enumerate(self.combos):
                    if i < len(self.event_waveform_names):
                        cb.current(i)

            self.reset_plots()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się przetworzyć pliku:\n{e}")

    def reset_plots(self):
        """Czyści wykresy i resetuje widok."""
        for ax in self.axes:
            ax.clear()
            ax.grid(True)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.canvas.draw()
        self.scroll_x.set(0, 1) # Reset scrolla

    def reset_ranges(self):
        """Czyści wszystkie pola zakresów i resetuje widok wykresów."""
        # Reset zakresu X
        self.entry_sample_start.delete(0, tk.END)
        self.entry_sample_end.delete(0, tk.END)
        self.current_window_size = None
        self.current_view_start = 0

        # Reset zakresów Y
        for e in self.y_min_entries:
            e.delete(0, tk.END)
        for e in self.y_max_entries:
            e.delete(0, tk.END)

        # Przerysowanie (jeśli jest co rysować)
        if self.current_selected_event_index:
            self.draw_waveforms()

    def on_update_click(self):
        idx_str = self.entry_event_idx.get().strip()
        
        if idx_str:
            self.current_selected_event_index = idx_str
            self.display_categorized_params()
            
            # Pobranie zakresu od użytkownika
            s_str = self.entry_sample_start.get().strip()
            e_str = self.entry_sample_end.get().strip()
            
            # Reset zmiennych widoku
            self.current_window_size = None
            self.current_view_start = 0
            
            # Parsowanie zakresu X
            user_start = 0
            user_end = None
            
            if s_str and e_str:
                try:
                    user_start = int(s_str)
                    user_end = int(e_str)
                    if user_start < user_end:
                        self.current_view_start = user_start
                        self.current_window_size = user_end - user_start
                except ValueError:
                    pass

            self.draw_waveforms()
        else:
            messagebox.showwarning("Uwaga", "Podaj numer zdarzenia.")

    def on_scroll_change(self, action, *args):
        """Obsługa zdarzenia przesunięcia paska przewijania."""
        if self.current_window_size is None or self.max_data_length == 0:
            return

        total_scrollable = self.max_data_length
        if total_scrollable <= self.current_window_size:
            return

        new_start = self.current_view_start

        if action == 'moveto':
            fraction = float(args[0])
            new_start = int(fraction * total_scrollable)
        elif action == 'scroll':
            count = int(args[0])
            step = max(1, int(self.current_window_size * 0.1))
            new_start += count * step

        max_start = total_scrollable - self.current_window_size
        if new_start < 0: 
            new_start = 0
        if new_start > max_start: 
            new_start = max_start
            
        self.current_view_start = new_start
        self.draw_waveforms(update_scroll_only=True)

    def draw_waveforms(self, update_scroll_only=False):
        """
        Rysuje wykresy.
        """
        event_idx = self.current_selected_event_index
        
        current_max_len = 0
        active_plots_data = [] 

        # Przygotowanie danych
        for i in range(4):
            selected_waveform = self.combos[i].get()
            data_points = None
            
            if selected_waveform and selected_waveform in self.event_waveform_values_map:
                events_data = self.event_waveform_values_map[selected_waveform]
                if event_idx in events_data:
                    y_values = events_data[event_idx]
                    data_len = len(y_values)
                    if data_len > current_max_len:
                        current_max_len = data_len
                    data_points = (range(data_len), y_values)
            
            active_plots_data.append((selected_waveform, data_points))

        self.max_data_length = current_max_len

        # Rysowanie
        for i in range(4):
            ax = self.axes[i]
            
            ax.clear()
            ax.grid(True)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True)) 
            ax.set_ylabel(f"Przebieg {i+1}") 

            name, points = active_plots_data[i]
            
            # Pobranie zakresu Y dla tego konkretnego wykresu
            y_min_str = self.y_min_entries[i].get().strip().replace(',', '.')
            y_max_str = self.y_max_entries[i].get().strip().replace(',', '.')
            y_limit = None
            
            if y_min_str and y_max_str:
                try:
                    y_min = float(y_min_str)
                    y_max = float(y_max_str)
                    if y_min < y_max:
                        y_limit = (y_min, y_max)
                except ValueError:
                    pass

            if not name:
                ax.set_title("Nie wybrano parametru")
                continue
            
            if points:
                x_vals, y_vals = points
                ax.plot(x_vals, y_vals, marker='o', markersize=2, linestyle='-')
                ax.set_title(f"{name} (Zdarzenie: {event_idx})", fontsize=9)
                
                # Ustawienie zakresu X
                if self.current_window_size is not None:
                    start = self.current_view_start
                    end = start + self.current_window_size
                    ax.set_xlim(start, end)
                
                # Ustawienie zakresu Y (jeśli podano)
                if y_limit:
                    ax.set_ylim(y_limit)

            else:
                ax.set_title(f"Brak danych lub zdarzenia {event_idx}")

        self.fig.tight_layout()
        self.canvas.draw()
        
        # Aktualizacja scrollbara
        if self.current_window_size is not None and self.max_data_length > 0:
            if self.current_window_size < self.max_data_length:
                first = self.current_view_start / self.max_data_length
                last = (self.current_view_start + self.current_window_size) / self.max_data_length
                self.scroll_x.set(first, last)
            else:
                self.scroll_x.set(0, 1)
        else:
            self.scroll_x.set(0, 1) 

    def extract_parameters(self, content, delimiter):
        """
        Parsuje parametry przy użyciu wykrytego separatora.
        """
        self.general_params = []
        self.event_data_names = []
        self.event_waveform_names = []
        self.event_data_values_map = {}
        self.event_waveform_values_map = {}

        lines = content.splitlines()
        if len(lines) > 0:
            lines = lines[1:]

        current_param_name = None
        current_data_lines = []

        def close_section():
            if current_param_name is not None:
                data_line_count = len(current_data_lines)

                # --- 1. PARAMETR OGÓLNY ---
                if data_line_count == 1:
                    val = "BRAK"
                    first_line = current_data_lines[0]
                    parts = first_line.split(delimiter)
                    valid_values = [p for p in parts[1:] if p.strip()]
                    if valid_values:
                        val = valid_values[0].strip()
                    self.general_params.append((current_param_name, val, len(valid_values)))
                
                # --- PARAMETR ZDARZEŃ ---
                elif data_line_count > 1:
                    first_line = current_data_lines[0]
                    parts = first_line.split(delimiter)
                    valid_values = [p for p in parts[1:] if p.strip()]
                    values_count_in_line = len(valid_values)

                    if values_count_in_line == 1:
                        # --- 2. DANE ZDARZEŃ ---
                        self.event_data_names.append(current_param_name)
                        values_map = {}
                        for dline in current_data_lines:
                            dparts = dline.split(delimiter)
                            if len(dparts) >= 2:
                                idx = dparts[0].strip()
                                val = dparts[1].strip()
                                if idx:
                                    values_map[idx] = val
                        self.event_data_values_map[current_param_name] = values_map

                    else:
                        # --- 3. PRZEBIEGI ZDARZEŃ ---
                        self.event_waveform_names.append(current_param_name)
                        waveform_map = {}
                        for dline in current_data_lines:
                            dparts = dline.split(delimiter)
                            idx = dparts[0].strip()
                            if not idx:
                                continue
                            numeric_values = []
                            for v_str in dparts[1:]:
                                v_clean = v_str.strip()
                                if v_clean:
                                    # Inteligentna konwersja float w zależności od separatora
                                    # Jeśli separator to ; (Polska), to decimal to prawdopodobnie ,
                                    if delimiter == ';':
                                        v_clean = v_clean.replace(',', '.')
                                    
                                    try:
                                        val_float = float(v_clean)
                                        numeric_values.append(val_float)
                                    except ValueError:
                                        pass 
                            waveform_map[idx] = numeric_values
                        self.event_waveform_values_map[current_param_name] = waveform_map

        for line in lines:
            # Sprawdzanie pustej linii używając wykrytego separatora
            is_separator_line = (line.replace(delimiter, '').strip() == "")

            if line.startswith("Event Index"):
                close_section()
                parts = line.split(delimiter)
                if len(parts) >= 2:
                    current_param_name = parts[1].strip()
                else:
                    current_param_name = "Nieznany"
                current_data_lines = []

            elif is_separator_line:
                close_section()
                current_param_name = None
                current_data_lines = []
            
            else:
                if current_param_name is not None:
                    current_data_lines.append(line)

        close_section()
        self.display_categorized_params()

    def display_categorized_params(self):
        self.params_text.delete(1.0, tk.END)

        # Sekcja 1
        self.params_text.insert(tk.END, "--- PARAMETRY OGÓLNE ---\n", "header")
        if self.general_params:
            for name, val, count in self.general_params:
                self.params_text.insert(tk.END, f"{name}: ")
                self.params_text.insert(tk.END, f"{val}\n", "value")
        else:
            self.params_text.insert(tk.END, "(brak)\n")
        self.params_text.insert(tk.END, "\n")

        # Sekcja 2
        self.params_text.insert(tk.END, "--- DANE ZDARZEŃ ---\n", "header")
        if self.event_data_names:
            for name in self.event_data_names:
                self.params_text.insert(tk.END, f"{name}")
                if self.current_selected_event_index is not None:
                    val_map = self.event_data_values_map.get(name, {})
                    found_val = val_map.get(self.current_selected_event_index)
                    if found_val is not None:
                        self.params_text.insert(tk.END, f": {found_val}", "event_val")
                self.params_text.insert(tk.END, "\n")
        else:
            self.params_text.insert(tk.END, "(brak)\n")
        self.params_text.insert(tk.END, "\n")

        # Sekcja 3
        self.params_text.insert(tk.END, "--- PRZEBIEGI ZDARZEŃ ---\n", "header")
        if self.event_waveform_names:
            for name in self.event_waveform_names:
                self.params_text.insert(tk.END, f"{name}\n")
        else:
            self.params_text.insert(tk.END, "(brak)\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = BlackBoxInterpreter(root)
    root.mainloop()