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
        
        # --- WERSJA APLIKACJI ---
        self.app_version = "1.0.0"
        self.root.title(f"Black Box Interpreter - ver. {self.app_version}")
        
        # --- Struktury danych ---
        self.general_params = []
        self.event_data_names = []
        self.event_waveform_names = []
        
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

        # --- TWORZENIE MENU ---
        self.create_menu()

        # ============================================================
        # GŁÓWNY SYSTEM ZAKŁADEK (Notebook)
        # ============================================================
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # --- ZAKŁADKA 1: Lista ogólna ---
        self.tab_general = tk.Frame(self.notebook)
        self.notebook.add(self.tab_general, text="Lista ogólna")
        self.setup_tab_general()

        # --- ZAKŁADKA 2: Przebiegi ---
        self.tab_waveforms = tk.Frame(self.notebook)
        self.notebook.add(self.tab_waveforms, text="Przebiegi")
        self.setup_tab_waveforms()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Załaduj plik alarmów", command=self.load_alarm_file)
        # ZMIANA: Zmiana nazwy i podpięcie funkcji
        file_menu.add_command(label="Załaduj plik przebiegów", command=self.load_waveform_file)
        file_menu.add_separator()
        file_menu.add_command(label="Wyjście", command=self.root.quit)
        menubar.add_cascade(label="Plik", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="O programie", command=self.show_about)
        menubar.add_cascade(label="Pomoc", menu=help_menu)

        self.root.config(menu=menubar)

    def setup_tab_general(self):
        """Konfiguracja zakładki 'Lista ogólna' - podział 50/50 Grid."""
        
        # Konfiguracja siatki dla idealnego podziału 50/50
        self.tab_general.grid_columnconfigure(0, weight=1, uniform="group1")
        self.tab_general.grid_columnconfigure(1, weight=1, uniform="group1")
        self.tab_general.grid_rowconfigure(0, weight=1)

        # --- PANEL LEWY (ALARMY) ---
        self.panel_alarms = tk.Frame(self.tab_general, bg="#e0e0e0", padx=10, pady=10)
        self.panel_alarms.grid(row=0, column=0, sticky="nsew")

        self.btn_load_alarms = tk.Button(
            self.panel_alarms, 
            text="Załaduj plik alarmów", 
            command=self.load_alarm_file,
            height=2, width=25
        )
        self.btn_load_alarms.pack(pady=(10, 10))

        tk.Label(self.panel_alarms, text="Lista zdarzeń (Alarmy):", bg="#e0e0e0", font=("Arial", 10, "bold")).pack(anchor="w")

        frame_txt_al = tk.Frame(self.panel_alarms)
        frame_txt_al.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        
        sc_y_al = tk.Scrollbar(frame_txt_al, orient=tk.VERTICAL)
        sc_x_al = tk.Scrollbar(frame_txt_al, orient=tk.HORIZONTAL)
        
        self.text_alarms_list = tk.Text(frame_txt_al, width=40, height=20, font=("Consolas", 9), wrap="none")
        
        sc_y_al.config(command=self.text_alarms_list.yview)
        sc_x_al.config(command=self.text_alarms_list.xview)
        self.text_alarms_list.config(yscrollcommand=sc_y_al.set, xscrollcommand=sc_x_al.set)
        
        self.text_alarms_list.grid(row=0, column=0, sticky="nsew")
        sc_y_al.grid(row=0, column=1, sticky="ns")
        sc_x_al.grid(row=1, column=0, sticky="ew")
        frame_txt_al.grid_rowconfigure(0, weight=1)
        frame_txt_al.grid_columnconfigure(0, weight=1)
        
        self.configure_text_tags(self.text_alarms_list)

        # --- PANEL PRAWY (PRZEBIEGI - PODGLĄD LISTY) ---
        self.panel_waveforms_list = tk.Frame(self.tab_general, bg="#dcdcdc", padx=10, pady=10)
        self.panel_waveforms_list.grid(row=0, column=1, sticky="nsew")

        self.btn_load_waveforms_gen = tk.Button(
            self.panel_waveforms_list, 
            text="Załaduj plik przebiegów", 
            command=self.load_waveform_file,
            height=2, width=25
        )
        self.btn_load_waveforms_gen.pack(pady=(10, 10))

        tk.Label(self.panel_waveforms_list, text="Lista zdarzeń (Przebiegi):", bg="#dcdcdc", font=("Arial", 10, "bold")).pack(anchor="w")

        frame_txt_wav = tk.Frame(self.panel_waveforms_list)
        frame_txt_wav.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        
        sc_y_wav = tk.Scrollbar(frame_txt_wav, orient=tk.VERTICAL)
        sc_x_wav = tk.Scrollbar(frame_txt_wav, orient=tk.HORIZONTAL)
        
        self.text_waveforms_list_preview = tk.Text(frame_txt_wav, width=40, height=20, font=("Consolas", 9), wrap="none")
        
        sc_y_wav.config(command=self.text_waveforms_list_preview.yview)
        sc_x_wav.config(command=self.text_waveforms_list_preview.xview)
        self.text_waveforms_list_preview.config(yscrollcommand=sc_y_wav.set, xscrollcommand=sc_x_wav.set)
        
        self.text_waveforms_list_preview.grid(row=0, column=0, sticky="nsew")
        sc_y_wav.grid(row=0, column=1, sticky="ns")
        sc_x_wav.grid(row=1, column=0, sticky="ew")
        frame_txt_wav.grid_rowconfigure(0, weight=1)
        frame_txt_wav.grid_columnconfigure(0, weight=1)

        self.configure_text_tags(self.text_waveforms_list_preview)

    def setup_tab_waveforms(self):
        """Konfiguracja zakładki 'Przebiegi'."""
        self.main_paned = tk.PanedWindow(self.tab_waveforms, orient=tk.HORIZONTAL, sashwidth=5, bg="#d0d0d0")
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # 1. PANEL LEWY (Dane tekstowe + Przycisk)
        self.panel_data = tk.Frame(self.main_paned, bg="#e0e0e0", padx=10, pady=10)
        self.main_paned.add(self.panel_data, minsize=350) 

        # 2. PANEL PRAWY (Wykresy i sterowanie)
        self.right_frame = tk.Frame(self.main_paned, bg="white")
        self.main_paned.add(self.right_frame, minsize=400) 

        # --- Podział Panelu Prawego (Góra/Dół) ---
        self.right_top_frame = tk.Frame(self.right_frame, height=160, bg="#f9f9f9", padx=10, pady=10)
        self.right_top_frame.pack(side=tk.TOP, fill=tk.X)
        self.right_top_frame.pack_propagate(False)

        self.right_bottom_frame = tk.Frame(self.right_frame, bg="white")
        self.right_bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # ================= ELEMENTY LEWEJ STRONY (PRZEBIEGI) =================
        
        # Przycisk
        self.upload_btn = tk.Button(
            self.panel_data, 
            text="Załaduj plik przebiegów", 
            command=self.load_waveform_file,
            height=2, width=25
        )
        self.upload_btn.pack(pady=(10, 10))

        # Etykieta
        lbl_data = tk.Label(self.panel_data, text="Zawartość pliku:", bg="#e0e0e0", font=("Arial", 10, "bold"))
        lbl_data.pack(anchor="w")

        # Kontener na tekst i scrollbary
        frame_text = tk.Frame(self.panel_data)
        frame_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

        scroll_y = tk.Scrollbar(frame_text, orient=tk.VERTICAL)
        scroll_x = tk.Scrollbar(frame_text, orient=tk.HORIZONTAL)

        self.text_main = tk.Text(frame_text, width=40, height=20, font=("Consolas", 9), wrap="none")
        
        scroll_y.config(command=self.text_main.yview)
        scroll_x.config(command=self.text_main.xview)
        self.text_main.config(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.text_main.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        
        frame_text.grid_rowconfigure(0, weight=1)
        frame_text.grid_columnconfigure(0, weight=1)

        self.configure_text_tags(self.text_main)

        # ================= ELEMENTY PRAWEJ STRONY (Bez zmian) =================
        
        row1 = tk.Frame(self.right_top_frame, bg="#f9f9f9")
        row1.pack(side=tk.TOP, fill=tk.X, pady=5)

        lbl_event_idx = tk.Label(row1, text="Numer zdarzenia:", bg="#f9f9f9", font=("Arial", 10))
        lbl_event_idx.pack(side=tk.LEFT, padx=(0, 5))

        self.entry_event_idx = tk.Spinbox(row1, from_=0, to=1000000, width=10)
        self.entry_event_idx.pack(side=tk.LEFT, padx=5)

        tk.Label(row1, text=" | ", bg="#f9f9f9", fg="gray").pack(side=tk.LEFT, padx=10)

        lbl_range = tk.Label(row1, text="Zakres próbek (X):", bg="#f9f9f9", font=("Arial", 10))
        lbl_range.pack(side=tk.LEFT, padx=(0, 5))

        self.entry_sample_start = tk.Spinbox(row1, from_=0, to=1000000, width=6)
        self.entry_sample_start.pack(side=tk.LEFT, padx=2)

        tk.Label(row1, text="-", bg="#f9f9f9").pack(side=tk.LEFT)

        self.entry_sample_end = tk.Spinbox(row1, from_=0, to=1000000, width=6)
        self.entry_sample_end.pack(side=tk.LEFT, padx=2)

        tk.Label(row1, text=" | ", bg="#f9f9f9", fg="gray").pack(side=tk.LEFT, padx=10)

        btn_update = tk.Button(row1, text="Aktualizuj", command=self.on_update_click)
        btn_update.pack(side=tk.LEFT, padx=5)

        btn_reset = tk.Button(row1, text="Resetuj zakresy", command=self.reset_ranges)
        btn_reset.pack(side=tk.LEFT, padx=5)

        row2 = tk.Frame(self.right_top_frame, bg="#f9f9f9")
        row2.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.combos = []
        self.y_min_entries = []
        self.y_max_entries = []

        for i in range(4):
            col_frame = tk.Frame(row2, bg="#f9f9f9")
            col_frame.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

            lbl = tk.Label(col_frame, text=f"Przebieg {i+1}", bg="#f9f9f9", font=("Arial", 8, "bold"))
            lbl.pack(side=tk.TOP, anchor="w")

            cb = ttk.Combobox(col_frame, state="readonly", width=15)
            cb.pack(side=tk.TOP, fill=tk.X)
            self.combos.append(cb)

            y_frame = tk.Frame(col_frame, bg="#f9f9f9")
            y_frame.pack(side=tk.TOP, fill=tk.X, pady=2)

            tk.Label(y_frame, text="Y:", bg="#f9f9f9", font=("Arial", 8)).pack(side=tk.LEFT)
            entry_min = tk.Spinbox(y_frame, from_=-100000, to=100000, increment=1, width=5)
            entry_min.pack(side=tk.LEFT, padx=2)
            tk.Label(y_frame, text="-", bg="#f9f9f9").pack(side=tk.LEFT)
            entry_max = tk.Spinbox(y_frame, from_=-100000, to=100000, increment=1, width=5)
            entry_max.pack(side=tk.LEFT, padx=2)

            self.y_min_entries.append(entry_min)
            self.y_max_entries.append(entry_max)

        self.fig = plt.Figure(figsize=(6, 8), dpi=100)
        self.axes = []
        for i in range(4):
            ax = self.fig.add_subplot(4, 1, i+1)
            ax.set_ylabel(f"Przebieg {i+1}")
            ax.grid(True)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            self.axes.append(ax)

        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_bottom_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.scroll_x = tk.Scrollbar(self.right_bottom_frame, orient="horizontal", command=self.on_scroll_change)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.notebook.select(self.tab_waveforms)

    def configure_text_tags(self, text_widget):
        text_widget.tag_config("header", foreground="blue", font=("Arial", 10, "bold"))
        text_widget.tag_config("table_header", foreground="black", font=("Consolas", 9, "bold"))
        text_widget.tag_config("value", foreground="darkgreen", font=("Consolas", 9, "bold"))
        text_widget.tag_config("list_item", foreground="black", font=("Consolas", 8))
        text_widget.tag_config("info", foreground="gray", font=("Consolas", 8))
        text_widget.tag_config("event_val", foreground="blue", font=("Consolas", 9, "bold"))

    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("O programie")
        about_window.geometry("300x180")
        about_window.resizable(False, False)

        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 90
        about_window.geometry(f"+{x}+{y}")

        tk.Label(about_window, text="Black Box Interpreter", font=("Arial", 12, "bold")).pack(pady=(15, 5))
        tk.Label(about_window, text=f"Wersja: {self.app_version}").pack(pady=2)
        tk.Label(about_window, text="Kod: Gemini").pack(pady=2)
        tk.Label(about_window, text="Prompt: Mateusz Baran").pack(pady=2)
        
        tk.Button(about_window, text="OK", command=about_window.destroy, width=10).pack(pady=10)

    # --- OBSŁUGA PLIKÓW ---

    def load_alarm_file(self):
        file_path = filedialog.askopenfilename(
            title="Wybierz plik alarmów",
            filetypes=[("Pliki CSV", "*.csv"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            self.process_file(file_path, target="alarm")

    def load_waveform_file(self):
        file_path = filedialog.askopenfilename(
            title="Wybierz plik przebiegów",
            filetypes=[("Pliki CSV", "*.csv"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            self.process_file(file_path, target="waveform")

    def process_file(self, file_path, target):
        try:
            content = ""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='cp1250') as f:
                    content = f.read()

            detected_delimiter = ';'
            for line in content.splitlines():
                if line.startswith("Event Index"):
                    if ";" in line:
                        detected_delimiter = ';'
                    elif "," in line:
                        detected_delimiter = ','
                    break
            
            parsed_data = self.extract_parameters(content, detected_delimiter)

            if target == "alarm":
                self.update_alarm_panel(parsed_data)
            elif target == "waveform":
                self.general_params = parsed_data['general']
                self.event_data_names = parsed_data['data_names']
                self.event_waveform_names = parsed_data['waveform_names']
                self.event_data_values_map = parsed_data['data_map']
                self.event_waveform_values_map = parsed_data['waveform_map']

                self.current_selected_event_index = None
                self.entry_event_idx.delete(0, tk.END)
                self.entry_sample_start.delete(0, tk.END)
                self.entry_sample_end.delete(0, tk.END)
                
                for cb in self.combos:
                    cb.set('')
                    cb['values'] = self.event_waveform_names
                
                for e in self.y_min_entries:
                    e.delete(0, tk.END)
                for e in self.y_max_entries:
                    e.delete(0, tk.END)

                if self.event_waveform_names:
                    for i, cb in enumerate(self.combos):
                        if i < len(self.event_waveform_names):
                            cb.current(i)

                self.update_waveform_panel_preview(parsed_data)
                self.display_categorized_params()
                self.reset_plots()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się przetworzyć pliku:\n{e}")

    def update_alarm_panel(self, data):
        """Aktualizuje tekst w lewym panelu zakładki 'Lista ogólna'."""
        self.text_alarms_list.delete(1.0, tk.END)
        event_list_text = self.generate_event_list_text(data['data_map'])
        if event_list_text:
            lines = event_list_text.splitlines()
            if lines:
                self.text_alarms_list.insert(tk.END, lines[0] + "\n", "table_header")
                for line in lines[1:]:
                    self.text_alarms_list.insert(tk.END, line + "\n", "list_item")
        else:
            self.text_alarms_list.insert(tk.END, "(brak danych zdarzeń)", "info")

    def update_waveform_panel_preview(self, data):
        """Aktualizuje tekst w prawym panelu zakładki 'Lista ogólna'."""
        self.text_waveforms_list_preview.delete(1.0, tk.END)
        event_list_text = self.generate_event_list_text(data['data_map'])
        if event_list_text:
            lines = event_list_text.splitlines()
            if lines:
                self.text_waveforms_list_preview.insert(tk.END, lines[0] + "\n", "table_header")
                for line in lines[1:]:
                    self.text_waveforms_list_preview.insert(tk.END, line + "\n", "list_item")
        else:
            self.text_waveforms_list_preview.insert(tk.END, "(brak danych zdarzeń)", "info")

    def generate_event_list_text(self, value_map):
        """
        Generuje sformatowany tekst listy zdarzeń (tabela z wyrównaniem).
        """
        target_keys = {
            "dt": "date time",
            "da": "device alarm",
            "id": "unique alarm id"
        }
        found_params = {} 

        # 1. Mapowanie kluczy
        for real_name in value_map.keys():
            real_name_lower = real_name.lower()
            for key, target in target_keys.items():
                if target in real_name_lower:
                    found_params[key] = real_name
        
        # 2. Zbieranie indeksów
        all_indices = set()
        for real_name in found_params.values():
            if real_name in value_map:
                indices = value_map[real_name].keys()
                all_indices.update(indices)
        
        def safe_int(x):
            try: return int(x)
            except: return 0
        sorted_indices = sorted(list(all_indices), key=safe_int)

        if not sorted_indices:
            return None

        # 3. Przygotowanie danych do tabeli (lista list)
        table_data = []
        
        # Nagłówki
        headers = ["[Index]"]
        if 'dt' in found_params: headers.append("Date Time")
        if 'da' in found_params: headers.append("Device Alarm")
        if 'id' in found_params: headers.append("ID")
        table_data.append(headers)

        # Wiersze danych
        for idx in sorted_indices:
            row = [f"[{idx}]"]
            if 'dt' in found_params:
                row.append(value_map[found_params['dt']].get(idx, ""))
            if 'da' in found_params:
                row.append(value_map[found_params['da']].get(idx, ""))
            if 'id' in found_params:
                row.append(value_map[found_params['id']].get(idx, ""))
            table_data.append(row)

        # 4. Obliczanie szerokości kolumn
        col_widths = [0] * len(headers)
        for row in table_data:
            for i, val in enumerate(row):
                if len(val) > col_widths[i]:
                    col_widths[i] = len(val)

        # 5. Formatowanie (padding + separator)
        formatted_lines = []
        
        # Formatowanie nagłówka
        header_row = table_data[0]
        header_str = " | ".join(val.ljust(width) for val, width in zip(header_row, col_widths))
        formatted_lines.append(header_str)
        
        # Separator (opcjonalnie, dla lepszej czytelności)
        separator_row = ["-" * width for width in col_widths]
        separator_str = "-+-".join(separator_row)
        formatted_lines.append(separator_str)

        # Formatowanie danych
        for row in table_data[1:]:
            line_str = " | ".join(val.ljust(width) for val, width in zip(row, col_widths))
            formatted_lines.append(line_str)
        
        return "\n".join(formatted_lines)

    def extract_parameters(self, content, delimiter):
        general = []
        data_names = []
        waveform_names = []
        data_map = {}
        waveform_map = {}

        lines = content.splitlines()
        current_param_name = None
        current_data_lines = []

        def close_section():
            nonlocal current_param_name
            if current_param_name is not None:
                data_line_count = len(current_data_lines)

                if data_line_count == 1:
                    val = "BRAK"
                    first_line = current_data_lines[0]
                    parts = first_line.split(delimiter)
                    valid_values = [p for p in parts[1:] if p.strip()]
                    if valid_values:
                        val = valid_values[0].strip()
                    general.append((current_param_name, val, len(valid_values)))
                
                elif data_line_count > 1:
                    first_line = current_data_lines[0]
                    parts = first_line.split(delimiter)
                    valid_values = [p for p in parts[1:] if p.strip()]
                    values_count_in_line = len(valid_values)

                    if values_count_in_line == 1:
                        data_names.append(current_param_name)
                        v_map = {}
                        for dline in current_data_lines:
                            dparts = dline.split(delimiter)
                            if len(dparts) >= 2:
                                idx = dparts[0].strip()
                                val = dparts[1].strip()
                                if idx:
                                    v_map[idx] = val
                        data_map[current_param_name] = v_map

                    else:
                        waveform_names.append(current_param_name)
                        w_map = {}
                        for dline in current_data_lines:
                            dparts = dline.split(delimiter)
                            idx = dparts[0].strip()
                            if not idx:
                                continue
                            numeric_values = []
                            for v_str in dparts[1:]:
                                v_clean = v_str.strip()
                                if v_clean:
                                    if delimiter == ';':
                                        v_clean = v_clean.replace(',', '.')
                                    try:
                                        val_float = float(v_clean)
                                        numeric_values.append(val_float)
                                    except ValueError:
                                        pass 
                            w_map[idx] = numeric_values
                        waveform_map[current_param_name] = w_map

        for line in lines:
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
        
        return {
            'general': general,
            'data_names': data_names,
            'waveform_names': waveform_names,
            'data_map': data_map,
            'waveform_map': waveform_map
        }

    def display_categorized_params(self):
        self.text_main.delete(1.0, tk.END)

        self.text_main.insert(tk.END, "--- PARAMETRY OGÓLNE ---\n", "header")
        if self.general_params:
            for name, val, count in self.general_params:
                self.text_main.insert(tk.END, f"{name}: ")
                self.text_main.insert(tk.END, f"{val}\n", "value")
        else:
            self.text_main.insert(tk.END, "(brak)\n")

        self.text_main.insert(tk.END, "\n--- LISTA ZDARZEŃ ---\n", "header")
        event_list_text = self.generate_event_list_text(self.event_data_values_map)
        
        if event_list_text:
            lines = event_list_text.splitlines()
            if lines:
                self.text_main.insert(tk.END, lines[0] + "\n", "table_header")
                for line in lines[1:]:
                    self.text_main.insert(tk.END, line + "\n", "list_item")
        else:
             self.text_main.insert(tk.END, "(brak danych zdarzeń)\n", "info")

        self.text_main.insert(tk.END, "\n--- DANE ZDARZENIA ---\n", "header")
        if self.event_data_names:
            for name in self.event_data_names:
                self.text_main.insert(tk.END, f"{name}")
                if self.current_selected_event_index is not None:
                    val_map = self.event_data_values_map.get(name, {})
                    found_val = val_map.get(self.current_selected_event_index)
                    if found_val is not None:
                        self.text_main.insert(tk.END, f": {found_val}", "event_val")
                self.text_main.insert(tk.END, "\n")
        else:
            self.text_main.insert(tk.END, "(brak)\n")
        
        self.text_main.insert(tk.END, "\n--- DOSTĘPNE PRZEBIEGI ---\n", "header")
        if self.event_waveform_names:
            for name in self.event_waveform_names:
                self.text_main.insert(tk.END, f"{name}\n")
        else:
            self.text_main.insert(tk.END, "(brak)\n")

    def reset_plots(self):
        for ax in self.axes:
            ax.clear()
            ax.grid(True)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.canvas.draw()
        self.scroll_x.set(0, 1)

    def reset_ranges(self):
        self.entry_sample_start.delete(0, tk.END)
        self.entry_sample_end.delete(0, tk.END)
        self.current_window_size = None
        self.current_view_start = 0

        for e in self.y_min_entries:
            e.delete(0, tk.END)
        for e in self.y_max_entries:
            e.delete(0, tk.END)

        if self.current_selected_event_index:
            self.draw_waveforms()

    def on_update_click(self):
        idx_str = self.entry_event_idx.get().strip()
        
        if idx_str:
            self.current_selected_event_index = idx_str
            self.display_categorized_params()
            
            s_str = self.entry_sample_start.get().strip()
            e_str = self.entry_sample_end.get().strip()
            
            self.current_window_size = None
            self.current_view_start = 0
            
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
        event_idx = self.current_selected_event_index
        
        current_max_len = 0
        active_plots_data = [] 

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

        for i in range(4):
            ax = self.axes[i]
            
            ax.clear()
            ax.grid(True)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True)) 
            ax.set_ylabel(f"Przebieg {i+1}") 

            name, points = active_plots_data[i]
            
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
                
                if self.current_window_size is not None:
                    start = self.current_view_start
                    end = start + self.current_window_size
                    ax.set_xlim(start, end)
                
                if y_limit:
                    ax.set_ylim(y_limit)

            else:
                ax.set_title(f"Brak danych lub zdarzenia {event_idx}")

        self.fig.tight_layout()
        self.canvas.draw()
        
        if self.current_window_size is not None and self.max_data_length > 0:
            if self.current_window_size < self.max_data_length:
                first = self.current_view_start / self.max_data_length
                last = (self.current_view_start + self.current_window_size) / self.max_data_length
                self.scroll_x.set(first, last)
            else:
                self.scroll_x.set(0, 1)
        else:
            self.scroll_x.set(0, 1) 

    def dummy_action(self):
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = BlackBoxInterpreter(root)
    root.mainloop()