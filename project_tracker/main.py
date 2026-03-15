import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import database as db
import logic
import export
from tkinter import messagebox, filedialog
import os
import sqlite3
from datetime import datetime

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Project Tracker - Premium Edition")
        self.geometry("1100x700")

        # Initialize Data
        db.init_db()
        self.current_project_id = None

        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="PROJECT TRACKER", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.dashboard_button = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.show_dashboard)
        self.dashboard_button.grid(row=1, column=0, padx=20, pady=10)

        self.add_project_button = ctk.CTkButton(self.sidebar_frame, text="Nuevo Proyecto", command=self.open_add_project_dialog)
        self.add_project_button.grid(row=2, column=0, padx=20, pady=10)

        # Main Content Area
        self.main_view = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_view.grid_columnconfigure(0, weight=1)
        self.main_view.grid_rowconfigure(0, weight=1)

        self.show_dashboard()

    def clear_view(self):
        for widget in self.main_view.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_view()
        title = ctk.CTkLabel(self.main_view, text="Mis Proyectos", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=10)

        projects_frame = ctk.CTkScrollableFrame(self.main_view, width=800, height=500)
        projects_frame.pack(fill="both", expand=True, padx=20, pady=20)

        projects = db.get_projects()
        if not projects:
            no_proj = ctk.CTkLabel(projects_frame, text="No hay proyectos aún. ¡Crea uno!")
            no_proj.pack(pady=20)
        else:
            for p in projects:
                btn = ctk.CTkButton(projects_frame, text=f"{p[1]} (Meta: {p[3]})", 
                                    command=lambda pid=p[0]: self.show_project_detail(pid),
                                    height=50, font=ctk.CTkFont(size=16))
                btn.pack(pady=5, fill="x", padx=10)

    def show_project_detail(self, project_id):
        self.current_project_id = project_id
        self.clear_view()
        
        projects = db.get_projects()
        project = next(p for p in projects if p[0] == project_id)
        
        header = ctk.CTkFrame(self.main_view, fg_color="transparent")
        header.pack(fill="x", pady=10)
        
        title = ctk.CTkLabel(header, text=project[1], font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(side="left", padx=10)
        
        edit_btn = ctk.CTkButton(header, text="Editar Fecha Límite", width=150, command=self.open_edit_project_dialog)
        edit_btn.pack(side="right", padx=10)
        
        back_btn = ctk.CTkButton(header, text="Volver", width=100, command=self.show_dashboard)
        back_btn.pack(side="right", padx=10)

        # Content Split: Left (Info/Logs) | Right (Graph)
        content = ctk.CTkFrame(self.main_view, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        # Logs Section
        logs_frame = ctk.CTkFrame(content)
        logs_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(logs_frame, text="Avances", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=5)
        
        self.log_list = ctk.CTkScrollableFrame(logs_frame)
        self.log_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.update_log_list(project_id)

        add_log_btn = ctk.CTkButton(logs_frame, text="Agregar Avance", command=self.open_add_log_dialog)
        add_log_btn.pack(pady=10)

        # Right Side: Tabs for Graph and Planning
        tabs = ctk.CTkTabview(content)
        tabs.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        tab_graph = tabs.add("Gráfico de Progreso")
        tab_planning = tabs.add("Planeación (5 Etapas)")
        tab_tasks = tabs.add("Tareas To-Do")

        # Graph Tab
        self.plot_graph(project_id, tab_graph, project[2], project[3])
        
        # Export Buttons in Graph Tab
        export_frame = ctk.CTkFrame(tab_graph, fg_color="transparent")
        export_frame.pack(pady=10)
        
        ctk.CTkButton(export_frame, text="Exportar Excel", width=120, fg_color="#1e7e34", 
                      command=lambda: self.export_project("excel")).pack(side="left", padx=5)
        ctk.CTkButton(export_frame, text="Exportar Word", width=120, fg_color="#007bff",
                      command=lambda: self.export_project("word")).pack(side="left", padx=5)
        ctk.CTkButton(export_frame, text="Exportar Gráfico", width=120, fg_color="#ff6b35",
                      command=self.export_graph).pack(side="left", padx=5)

        # Planning Tab
        self.show_planning(project_id, tab_planning)

        # Tasks Tab
        self.show_tasks(project_id, tab_tasks)

    def show_planning(self, project_id, parent):
        ctk.CTkLabel(parent, text="Etapas Sugeridas para Entrega", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        stages = db.get_stages(project_id)
        for s in stages:
            status = "✅" if s[4] else "⏳"
            stage_frame = ctk.CTkFrame(parent)
            stage_frame.pack(fill="x", padx=20, pady=5)
            
            ctk.CTkLabel(stage_frame, text=f"{status} {s[2]}").pack(side="left", padx=10)
            ctk.CTkLabel(stage_frame, text=f"Vence: {s[3]}").pack(side="right", padx=10)

    def export_project(self, fmt):
        if not self.current_project_id: return
        
        if fmt == "excel":
            path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
            if path:
                export.export_to_excel(self.current_project_id, path)
                messagebox.showinfo("Éxito", "Reporte Excel guardado")
        else:
            path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word files", "*.docx")])
            if path:
                export.export_to_word(self.current_project_id, path)
                messagebox.showinfo("Éxito", "Reporte Word guardado")

    def export_graph(self):
        if not hasattr(self, 'current_fig') or self.current_fig is None:
            messagebox.showwarning("Advertencia", "No hay gráfico para exportar")
            return
        
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("SVG files", "*.svg")])
        if path:
            try:
                self.current_fig.savefig(path, bbox_inches='tight')
                messagebox.showinfo("Éxito", "Gráfico guardado")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el gráfico: {e}")

    def show_tasks(self, project_id, parent):
        for widget in parent.winfo_children():
            widget.destroy()
            
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=10)
        ctk.CTkLabel(header, text="Mi lista de pendientes", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        
        add_btn = ctk.CTkButton(header, text="+ Tarea", width=80, command=self.open_add_task_dialog)
        add_btn.pack(side="right", padx=10)

        tasks_scroll = ctk.CTkScrollableFrame(parent)
        tasks_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        tasks = db.get_tasks(project_id)
        for t in tasks:
            t_frame = ctk.CTkFrame(tasks_scroll)
            t_frame.pack(fill="x", pady=2, padx=5)
            
            check_var = ctk.BooleanVar(value=bool(t[3]))
            cb = ctk.CTkCheckBox(t_frame, text=t[2], variable=check_var, 
                                 command=lambda tid=t[0], var=check_var: self.toggle_task_status(tid, var))
            cb.pack(side="left", padx=10, pady=5)

    def toggle_task_status(self, task_id, var):
        db.toggle_task(task_id, int(var.get()))
        # Refresh graph if user is looking at it? 
        # For now, let's just update the DB. Next time they open the detail it refreshes.
        # Or we could call show_project_detail again but that's expensive.
        # Let's just notify that it affects progress.

    def open_add_task_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nueva Tarea")
        dialog.geometry("350x200")
        dialog.attributes("-topmost", True)

        ctk.CTkLabel(dialog, text="Descripción:").pack(pady=(20, 0))
        entry = ctk.CTkEntry(dialog, width=250)
        entry.pack(pady=5)

        def save():
            save_button.configure(state="disabled")  # Disable button to prevent multiple clicks
            desc = entry.get()
            if desc:
                db.add_task(self.current_project_id, desc)
                dialog.destroy()
                self.show_project_detail(self.current_project_id)
            
        save_button = ctk.CTkButton(dialog, text="Guardar", command=save)
        save_button.pack(pady=20)

    def update_log_list(self, project_id):
        for widget in self.log_list.winfo_children():
            widget.destroy()
        
        logs = db.get_logs(project_id)
        for l in reversed(logs):
            score_text = "Menor" if l[4] == 1 else "Mayor" if l[4] == 5 else "Ninguno"
            log_item = ctk.CTkLabel(self.log_list, text=f"{l[2][:10]} - {score_text}\n{l[3]}", 
                                    justify="left", anchor="w", wraplength=250)
            log_item.pack(fill="x", pady=5, padx=5)

    def plot_graph(self, project_id, parent, start_date, end_date):
        logs = db.get_logs(project_id)
        tasks = db.get_tasks(project_id)
        dates, values = logic.process_graph_data(logs, tasks, start_date, end_date)
        
        if not dates:
            ctk.CTkLabel(parent, text="Agrega avances para ver el gráfico").pack(expand=True)
            self.current_fig = None  # No figure to export
            return

        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        
        ax.plot(dates, values, marker='o', color='#1f6aa5', linewidth=2)
        ax.tick_params(axis='x', colors='white', labelsize=8)
        ax.tick_params(axis='y', colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, linestyle='--', alpha=0.3)
        
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
        fig.tight_layout()

        self.current_fig = fig  # Store the figure for export

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def open_add_project_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Añadir Proyecto")
        dialog.geometry("400x300")
        dialog.attributes("-topmost", True)

        ctk.CTkLabel(dialog, text="Nombre del Proyecto:").pack(pady=(20, 0))
        name_entry = ctk.CTkEntry(dialog, width=250)
        name_entry.pack(pady=5)

        ctk.CTkLabel(dialog, text="Fecha Límite (YYYY-MM-DD):").pack(pady=(10, 0))
        date_entry = ctk.CTkEntry(dialog, width=250)
        date_entry.pack(pady=5)

        def save():
            save_button.configure(state="disabled")  # Disable button to prevent multiple clicks
            name = name_entry.get()
            date = date_entry.get()
            if name and date:
                try:
                    pid = db.add_project(name, date)
                    # Automatically generate 5 stages
                    today = datetime.now().strftime("%Y-%m-%d")
                    stages = logic.calculate_stages(today, date)
                    for s in stages:
                        db.add_stage(pid, s['name'], s['due_date'])
                    
                    dialog.destroy()
                    self.show_dashboard()
                except Exception as e:
                    messagebox.showerror("Error", f"Fecha inválida: {e}")
                    save_button.configure(state="normal")  # Re-enable on error
            else:
                messagebox.showwarning("Advertencia", "Completa todos los campos")
                save_button.configure(state="normal")  # Re-enable if incomplete

        save_button = ctk.CTkButton(dialog, text="Guardar", command=save)
        save_button.pack(pady=20)

    def open_add_log_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Añadir Avance")
        dialog.geometry("400x350")
        dialog.attributes("-topmost", True)

        ctk.CTkLabel(dialog, text="Descripción:").pack(pady=(20, 0))
        desc_entry = ctk.CTkTextbox(dialog, height=100, width=300)
        desc_entry.pack(pady=5)

        ctk.CTkLabel(dialog, text="Nivel de Avance:").pack(pady=(10, 0))
        level_var = ctk.StringVar(value="Menor")
        ctk.CTkOptionMenu(dialog, variable=level_var, values=["Menor", "Mayor", "Ninguno"]).pack(pady=5)

        def save():
            save_button.configure(state="disabled")  # Disable button to prevent multiple clicks
            desc = desc_entry.get("1.0", "end-1c")
            level = level_var.get()
            score = 1 if level == "Menor" else 5 if level == "Mayor" else 0
            
            if desc.strip():
                db.add_log(self.current_project_id, desc, score)
                dialog.destroy()
                self.show_project_detail(self.current_project_id)
            else:
                messagebox.showwarning("Advertencia", "La descripción está vacía")
                save_button.configure(state="normal")  # Re-enable if empty

        save_button = ctk.CTkButton(dialog, text="Agregar", command=save)
        save_button.pack(pady=20)

    def open_edit_project_dialog(self):
        projects = db.get_projects()
        project = next(p for p in projects if p[0] == self.current_project_id)
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Editar Fecha Límite")
        dialog.geometry("400x200")
        dialog.attributes("-topmost", True)

        ctk.CTkLabel(dialog, text=f"Proyecto: {project[1]}").pack(pady=(20, 10))
        
        ctk.CTkLabel(dialog, text="Nueva Fecha Límite (YYYY-MM-DD):").pack(pady=(10, 0))
        date_entry = ctk.CTkEntry(dialog, width=250)
        date_entry.insert(0, project[3])  # Pre-fill with current deadline
        date_entry.pack(pady=5)

        def save():
            save_button.configure(state="disabled")  # Disable button to prevent multiple clicks
            new_date = date_entry.get()
            if new_date:
                try:
                    db.update_project_deadline(self.current_project_id, new_date)
                    # Use only the date part (YYYY-MM-DD) from created_at
                    created_date = project[2].split()[0] if project[2] else ""
                    stages = logic.calculate_stages(created_date, new_date)
                    # Delete old stages and add new ones
                    conn = sqlite3.connect(db.DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM stages WHERE project_id = ?", (self.current_project_id,))
                    for s in stages:
                        cursor.execute("INSERT INTO stages (project_id, name, due_date) VALUES (?, ?, ?)", 
                                     (self.current_project_id, s['name'], s['due_date']))
                    conn.commit()
                    conn.close()
                    
                    dialog.destroy()
                    self.show_project_detail(self.current_project_id)
                    messagebox.showinfo("Éxito", "Fecha límite actualizada")
                except Exception as e:
                    messagebox.showerror("Error", f"Fecha inválida: {e}")
                    save_button.configure(state="normal")  # Re-enable on error
            else:
                messagebox.showwarning("Advertencia", "Ingresa una fecha")
                save_button.configure(state="normal")  # Re-enable if empty

        save_button = ctk.CTkButton(dialog, text="Guardar", command=save)
        save_button.pack(pady=20)

if __name__ == "__main__":
    from datetime import datetime
    app = App()
    app.mainloop()
