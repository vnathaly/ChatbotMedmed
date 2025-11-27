import os
import sys
from google import genai
from google.genai import types
from PIL import Image, ImageTk
from dotenv import load_dotenv
import tkinter as tk
from tkinter import filedialog, ttk

load_dotenv()

try:
    client = genai.Client()
except Exception as e:
    print("Error al inicializar el cliente de Gemini, Favor intente de nuevo en unos minutos.")
    sys.exit(1)

chat_session = None

def inicializar_chat():
    """Inicializa un nuevo objeto de chat con el modelo Gemini"""
    global chat_session
    try:
        chat_session = client.chats.create(model='gemini-2.5-flash')
        return "¡Hola! Soy medmed, tu asistente medico multimodal. ¿En qué puedo ayudarte hoy?"
    except Exception as e:
        return f"Error al crear la sesión de chat: {e}"

def procesar_entrada(entrada: str, ruta_imagen: str = None):
    """
    Envía la entrada al modelo (texto puro o texto + imagen) y actualiza el historial de chat.
    """
    global chat_session

    contents = []

    # 1. Procesar Imagen (si existe una ruta válida)
    if ruta_imagen:
        try:
            imagen = Image.open(ruta_imagen)
            contents.append(imagen)
            print("Imagen cargada correctamente.")
        except FileNotFoundError:
            return f"Error: No se encontró el archivo de imagen en la ruta: {ruta_imagen}. Verifique la ruta."
        except Exception as e:
            return f"Error al abrir la imagen: {e}"
    
    # 2. Procesar Texto
    if not entrada:
        # Si no hay imagen, debe haber texto.
        return "Por favor, ingresa una pregunta o instrucción."
        
    contents.append(entrada)

    # 3. Enviar mensaje
    try:
        response = chat_session.send_message(contents)
        return response.text
    except Exception as e:
        return f"Error de la API: {e}"

# --------------------------------------------------------------------------------
# --- 1. CONFIGURACIÓN DE LA INTERFAZ (TKINTER) ---
# --------------------------------------------------------------------------------

class ChatbotUI(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # --- Configuración de la Ventana ---
        self.title("medmed - Asistente Multimodal")
        self.geometry("1000x650") 
        self.configure(bg="#F8F8F8")
        
        # Estilos generales para replicar la apariencia moderna
        self.style = ttk.Style(self)
        self.style.theme_use('default') 
        # Configurar colores que simulen el diseño
        self.style.configure('TFrame', background='#F8F8F8')
        self.style.configure('TLabel', background='#F8F8F8', foreground='#333')
        
        # Variables de estado
        self.chat_initialized = False
        self.current_image_path = None
        
        # --- CARGAR ICONO DEL ROBOT ---
        self.robot_icon = None
        try:
            # Asegúrate de que 'robot_icon.png' esté en la misma carpeta
            self.robot_img_pil = Image.open("robot_icon.png")
            # Redimensionar el icono del bot (ej: 30x30 píxeles para el chat)
            self.robot_img_pil = self.robot_img_pil.resize((30, 30), Image.Resampling.LANCZOS)
            self.robot_icon = ImageTk.PhotoImage(self.robot_img_pil)
        except FileNotFoundError:
            print("AVISO: No se encontró 'robot_icon.png'. Los mensajes del bot no tendrán icono.")
        except Exception as e:
            print(f"Error al cargar el icono del robot: {e}")
        
        # Inicializar el chat de Gemini (se hace al arrancar la UI)
        self.initial_message = inicializar_chat()
        
        self.create_widgets()

    def create_widgets(self):
        # --- Contenedor Principal (Simula la Ventana de Chat) ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # --- 1. SIDEBAR (Columna Izquierda: Logo y Botón Inicio) ---
        sidebar = ttk.Frame(main_frame, width=200, style='TFrame', relief='flat')
        sidebar.pack(side="left", fill="y", padx=10, pady=10)
        sidebar.configure(style='Sidebar.TFrame') # Estilo para fondo verde

        # Definir estilos de color para sidebar
        self.style.configure('Sidebar.TFrame', background='#4CAF50') # Verde primario

        # Logo y Nombre
        logo_label = ttk.Label(sidebar, text="medmed", font=('Arial', 18, 'bold'), 
                               foreground='white', background='#4CAF50')
        logo_label.pack(pady=(20, 40), padx=20, anchor='center')

        # Botón Inicio
        home_button = ttk.Button(sidebar, text=" Inicio", style='Home.TButton')
        home_button.pack(fill='x', padx=10, pady=5)
        
        # Estilo para el botón Home activo
        self.style.configure('Home.TButton', background='#90EE90', foreground='#333', 
                             font=('Arial', 11), borderwidth=0)
        self.style.map('Home.TButton', background=[('active', '#90EE90')])

        # --- 2. CHAT MAIN (Columna Derecha) ---
        chat_frame = ttk.Frame(main_frame, style='TFrame')
        chat_frame.pack(side="right", fill="both", expand=True)

        # --- Área de Mensajes (Scrolleable) ---
        self.messages_canvas = tk.Canvas(chat_frame, bg="#FFFFFF", highlightthickness=0)
        self.messages_canvas.pack(fill="both", expand=True, padx=10, pady=5)

        self.messages_frame = ttk.Frame(self.messages_canvas, style='TFrame', padding="10 0 10 0")
        
        self.messages_canvas.create_window((0, 0), window=self.messages_frame, anchor="nw")
        
        # Configurar scrollbar
        v_scrollbar = ttk.Scrollbar(self.messages_canvas, orient="vertical", command=self.messages_canvas.yview)
        v_scrollbar.pack(side="right", fill="y")
        self.messages_canvas.configure(yscrollcommand=v_scrollbar.set)
        self.messages_frame.bind("<Configure>", lambda e: self.messages_canvas.configure(scrollregion=self.messages_canvas.bbox("all")))
        
        # Mensaje de Bienvenida inicial
        self.display_message("bot", self.initial_message)

        # --- Área de Entrada (Abajo) ---
        input_area = ttk.Frame(chat_frame, style='TFrame', padding="10")
        input_area.pack(fill="x", pady=(0, 10))

        # Botón de adjuntar imagen (Simula el envío de ruta)
        attach_button = ttk.Button(input_area, text="🖼️ Adjuntar", command=self.select_image_path)
        attach_button.pack(side="left", padx=(0, 5))
        
        # Campo de entrada
        self.input_entry = ttk.Entry(input_area, font=('Arial', 12))
        self.input_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.input_entry.bind("<Return>", lambda event: self.send_message()) # Enviar con Enter

        # Botón de enviar
        send_button = ttk.Button(input_area, text="Enviar", command=self.send_message)
        send_button.pack(side="left", padx=(5, 0))
        
        # Etiqueta de aviso legal
        disclaimer_label = ttk.Label(chat_frame, 
                                     text="medmed es un Asistente IA y no proporciona diagnóstico médico. Para emergencias, contacte servicios de emergencia.",
                                     font=('Arial', 8), foreground='#999')
        disclaimer_label.pack(fill='x', pady=5)


    # --------------------------------------------------------------------------------
    # --- 3. LÓGICA DE LA INTERFAZ ---
    # --------------------------------------------------------------------------------

    def select_image_path(self):
        """Abre un diálogo para seleccionar un archivo de imagen."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar Imagen",
            filetypes=(("Archivos de Imagen", "*.png;*.jpg;*.jpeg"), ("Todos los archivos", "*.*"))
        )
        if file_path:
            self.current_image_path = file_path
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, f"🖼️ Imagen adjunta: {os.path.basename(file_path)}")
            self.input_entry.focus()

    def display_message(self, sender, text, image_path=None):
        """Muestra un mensaje (y opcionalmente una imagen) en la interfaz."""
        
        # Crear un marco para el mensaje completo (para alineación)
        msg_frame = ttk.Frame(self.messages_frame, style='TFrame')
        msg_frame.pack(fill='x', pady=5, padx=5, anchor='w' if sender == 'bot' else 'e')

        # Estilo de la burbuja y alineación
        bubble_color = '#90EE90' if sender == 'user' else 'white'
        bubble_anchor = 'e' if sender == 'user' else 'w'
        
        bubble_style = ttk.Style()
        bubble_style.configure(f'{sender}.Bubble.TFrame', background=bubble_color, borderwidth=1, relief='flat', 
                               padding=10, bordercolor='#E0E0E0' if sender == 'bot' else bubble_color)
        
        # *** NUEVO: Contenedor para Icono + Burbuja para Mensajes del BOT ***
        if sender == 'bot':
            bot_container = ttk.Frame(msg_frame, style='TFrame')
            bot_container.pack(side='left', anchor='nw')

            # 1. Mostrar Icono del Robot (Si está cargado)
            if self.robot_icon:
                icon_label = ttk.Label(bot_container, image=self.robot_icon, background='#F8F8F8')
                icon_label.image = self.robot_icon # Mantener referencia
                icon_label.pack(side="left", padx=(0, 5), anchor='n')

            # 2. Burbuja del mensaje del Bot
            bubble = ttk.Frame(bot_container, style=f'{sender}.Bubble.TFrame')
            bubble.pack(side='left', fill='y', padx=10)
        else:
            # Mensajes del Usuario (sin icono)
            bubble = ttk.Frame(msg_frame, style=f'{sender}.Bubble.TFrame')
            bubble.pack(side='right', fill='y', padx=10)

        
        # Mostrar imagen si existe (Dentro de la burbuja)
        if image_path and os.path.exists(image_path):
            try:
                # Mostrar la imagen en miniatura
                img = Image.open(image_path)
                img = img.resize((150, 150), Image.Resampling.LANCZOS)
                self.tk_image = ImageTk.PhotoImage(img) # Necesario para que Tkinter no la borre
                
                img_label = ttk.Label(bubble, image=self.tk_image, style='TLabel')
                img_label.image = self.tk_image # Referencia
                img_label.pack(pady=(0, 10))
            except Exception as e:
                text = f"Error al mostrar la imagen: {e}\n\n{text}"

        # Texto del mensaje
        msg_label = ttk.Label(bubble, text=text, wraplength=400, font=('Arial', 10), 
                              background=bubble_color, foreground='#333')
        msg_label.pack(pady=5, padx=5, anchor='w') # Usamos 'w' para que el texto siempre se alinee a la izquierda dentro de la burbuja

        
        # Desplazar el scroll al final
        self.messages_canvas.update_idletasks()
        self.messages_canvas.yview_moveto(1.0)


    def send_message(self):
        """Función principal que maneja la entrada del usuario, llama a la API y muestra la respuesta."""
        
        user_input = self.input_entry.get().strip()
        
        if not user_input:
            return

        # 1. Obtener los parámetros de la entrada
        if self.current_image_path:
            # Si hay una imagen adjunta, la pregunta es el texto de la entrada (sin el aviso)
            question = user_input.replace(f"🖼️ Imagen adjunta: {os.path.basename(self.current_image_path)}", "").strip()
            # Si el usuario borra la pregunta, ponemos una por defecto para la imagen
            if not question:
                 question = "Describe esta imagen."
            
            # Mostrar el mensaje del usuario (con la imagen)
            self.display_message("user", question, image_path=self.current_image_path)
            
            # Llamar a la API
            api_response = procesar_entrada(question, self.current_image_path)
            
            # Limpiar la ruta después de enviar
            self.current_image_path = None 
        else:
            # Modo Conversación (solo texto)
            self.display_message("user", user_input)
            api_response = procesar_entrada(user_input, None)
            
        # 2. Limpiar la entrada y mostrar la respuesta de la API
        self.input_entry.delete(0, tk.END)
        self.display_message("bot", api_response)


if __name__ == "__main__":
    app = ChatbotUI()
    app.mainloop()