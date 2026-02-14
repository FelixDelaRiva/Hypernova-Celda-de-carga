import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import threading
import time
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from fpdf import FPDF
from datetime import datetime

import os

PORT = "COM4"
BAUDRATE = 115200
RUNNING = False
DATA = []

def read_serial():
    global RUNNING, DATA
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        while RUNNING:
            line = ser.readline().decode('utf-8').strip()
            if line:
                try:
                    t, peso, kgps = map(float, line.split(","))
                    DATA.append((t, peso, kgps))
                    update_plot()
                except ValueError:
                    pass
        ser.close()
    except serial.SerialException:
        messagebox.showerror("Error", f"No se pudo abrir el puerto {PORT}")

# --- Funciones para botones ---
def start_test():
    global RUNNING, DATA, start_time_str
    if RUNNING:
        return
    RUNNING = True
    DATA.clear()
    now = datetime.now()
    entry_pc_time.config(state='normal')
    entry_pc_time.delete(0, tk.END)
    entry_pc_time.insert(0, now.strftime("%H:%M:%S"))
    entry_pc_time.config(state='readonly')
    start_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    threading.Thread(target=read_serial, daemon=True).start()

def stop_test():
    global RUNNING
    RUNNING = False

def reset_data():
    global DATA, RUNNING
    RUNNING = False
    DATA.clear()
    ax.clear()
    ax.set_title("Peso y Cambio en Tiempo Real")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Peso (kg)")
    canvas.draw()

def export_data():
    if not DATA:
        messagebox.showwarning("Advertencia", "No hay datos para exportar.")
        return
    df = pd.DataFrame(DATA, columns=["Tiempo (s)", "Peso (kg)", "Cambio (kg/s)"])

    # CSV
    filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not filename:
        return
    df.to_csv(filename, index=False)

    # Guardar imagen del gráfico
    graph_image = filename.replace(".csv", "_grafico.png")
    fig.savefig(graph_image)

    # PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Reporte de Prueba - Celda de Carga", ln=True, align="C")
    pdf.set_font("Arial", "", 10)

    fields = {
        "Día": entry_dia.get(),
        "Hora de inicio": entry_hora.get(),
        "Hora PC": entry_pc_time.get(),
        "N° Prueba": entry_num_prueba.get(),
        "Responsable": entry_responsable.get()
    }

    for key, val in fields.items():
        pdf.cell(0, 10, f"{key}: {val}", ln=True)

    pdf.ln(5)
    pdf.image(graph_image, x=10, y=pdf.get_y(), w=180)
    pdf.ln(95)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(60, 8, "Tiempo (s)", 1)
    pdf.cell(60, 8, "Peso (kg)", 1)
    pdf.cell(60, 8, "Cambio (kg/s)", 1)
    pdf.ln()

    pdf.set_font("Arial", "", 9)
    for row in DATA:
        pdf.cell(60, 8, f"{row[0]:.2f}", 1)
        pdf.cell(60, 8, f"{row[1]:.2f}", 1)
        pdf.cell(60, 8, f"{row[2]:.2f}", 1)
        pdf.ln()

    pdf.output(filename.replace(".csv", ".pdf"))
    os.remove(graph_image)
    messagebox.showinfo("Exportado", "Datos exportados a CSV y PDF correctamente.")

# --- Función para actualizar la gráfica ---
def update_plot():
    if not DATA:
        return
    times, pesos, velocidades = zip(*DATA)
    ax.clear()
    ax.plot(times, pesos, label="Peso (kg)", color="blue")
    ax.plot(times, velocidades, label="Cambio (kg/s)", color="green")
    ax.set_title("Peso y Cambio en Tiempo Real")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Valores")
    ax.legend()
    canvas.draw()

# --- GUI con Tkinter ---
root = tk.Tk()
root.title("Adquisición de Datos - Celda de Carga")

# Entradas
frm_input = ttk.Frame(root)
frm_input.pack(padx=10, pady=5)

labels = ["Día", "Hora de Inicio", "Hora PC", "N° Prueba", "Responsable"]
entries = []
for i, lbl in enumerate(labels):
    ttk.Label(frm_input, text=lbl).grid(row=i, column=0, sticky="w")
    entry = ttk.Entry(frm_input, width=30)
    entry.grid(row=i, column=1)
    entries.append(entry)

entry_dia, entry_hora, entry_pc_time, entry_num_prueba, entry_responsable = entries
entry_pc_time.config(state='readonly')  # Desactivar edición manual

# Botones
frm_buttons = ttk.Frame(root)
frm_buttons.pack(pady=10)

ttk.Button(frm_buttons, text="▶ Iniciar Prueba", command=start_test).grid(row=0, column=0, padx=5)
ttk.Button(frm_buttons, text="■ Detener", command=stop_test).grid(row=0, column=1, padx=5)
ttk.Button(frm_buttons, text="🔄 Reset", command=reset_data).grid(row=0, column=2, padx=5)
ttk.Button(frm_buttons, text="💾 Exportar", command=export_data).grid(row=0, column=3, padx=5)

# Gráfica
fig, ax = plt.subplots(figsize=(7, 4))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(pady=10)
ax.set_title("Peso y Cambio en Tiempo Real")
ax.set_xlabel("Tiempo (s)")
ax.set_ylabel("Valores")
canvas.draw()

# Ejecutar
root.mainloop()
