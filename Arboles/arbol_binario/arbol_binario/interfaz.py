"""
interfaz.py
===========
Ventana principal de la aplicación (Tkinter).

Organización de la ventana
--------------------------
* **A. Panel lateral (izquierda)**: campo de valor y botones de operaciones.
* **B. Área central**: ``Canvas`` con el árbol, resultados de recorridos y leyenda.
* **C. Panel de información (derecha)**: estadísticas, estado y recorridos.

La interfaz llama directamente a los métodos reales de ``Arbol``; no simula
ninguna operación. Mientras corre una animación los botones se bloquean para
evitar operaciones simultáneas (estabilidad).
"""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from arbol import Arbol
from visualizador import ESTILOS, Visualizador

# ----------------------------------------------------------------------
# Paleta (tema oscuro)
# ----------------------------------------------------------------------
BG = "#0f1220"          # fondo de la ventana
PANEL = "#171b2e"       # paneles laterales
PANEL2 = "#1f2442"      # tarjetas / campos
LIENZO = "#121629"      # fondo del canvas
BORDE = "#2e3560"
TEXTO = "#e8eaf6"
APAGADO = "#8a91b4"
ACENTO = "#6c63ff"
EXITO = "#2ecc9a"
PELIGRO = "#ff5c7a"
AVISO = "#ffb454"
INFO = "#4cc9f0"

COLORES_ESTADO = {"info": INFO, "success": EXITO, "warning": AVISO, "error": PELIGRO}

RECORRIDOS = {
    "preorden": ("Preorden", "Raíz · Izq · Der"),
    "inorden": ("Inorden", "Izq · Raíz · Der"),
    "postorden": ("Postorden", "Izq · Der · Raíz"),
    "niveles": ("Por niveles", "Amplitud"),
}
RETARDOS = {1: 900, 2: 650, 3: 450, 4: 260, 5: 130}      # ms por paso según velocidad
VALOR_MAX = 9999
EJEMPLO = [50, 30, 70, 20, 40, 60, 80, 35, 45, 65]


class AplicacionArbol(tk.Tk):
    """Ventana principal: administra un ``Arbol`` y lo muestra con un ``Visualizador``."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Árbol Binario de Búsqueda · Visualizador interactivo")
        ancho = min(1340, self.winfo_screenwidth() - 60)
        alto = min(800, max(700, self.winfo_screenheight() - 60))
        self.geometry(f"{ancho}x{alto}+20+20")
        self.minsize(1100, 700)
        self.configure(bg=BG)

        self.fam = tkfont.nametofont("TkDefaultFont").actual()["family"]
        self.arbol = Arbol()
        self._ocupado = False
        self._botones: list[ttk.Button] = []
        self._generacion = 0                 # invalida «limpiezas» pendientes
        self._id_redibujo = None

        self.var_valor = tk.StringVar()
        self.var_velocidad = tk.DoubleVar(value=3)
        self.var_recorrido = {k: tk.StringVar(value="—") for k in RECORRIDOS}
        self.var_stats = {k: tk.StringVar(value="—") for k in
                          ("nodos", "altura", "hojas", "minimo", "maximo", "raiz")}
        self.var_estado_arbol = tk.StringVar()
        self.var_mensaje = tk.StringVar()

        self._configurar_estilos()
        self._crear_widgets()
        self.vis = Visualizador(self.canvas, color_arista="#4a5188", color_vacio=APAGADO,
                                al_clic_nodo=self._al_clic_nodo)
        self._refrescar()
        self._mostrar_estado("Bienvenido. Inserta un valor o genera un árbol de ejemplo.", "info")
        self.entrada.focus_set()

    # ==================================================================
    # Estilos ttk
    # ==================================================================
    def _configurar_estilos(self) -> None:
        e = ttk.Style(self)
        e.theme_use("clam")
        fam = self.fam
        botones = {
            "Acento": (ACENTO, "#8179ff", "#554cdb"),
            "Info": ("#2a77c9", "#3b8de0", "#1f5fa8"),
            "Neutro": ("#2a3060", "#38407a", "#222850"),
            "Peligro": ("#d6455f", "#ee5c76", "#b1344b"),
            "Exito": ("#1fa77b", "#2bc795", "#17855f"),
        }
        for nombre, (bg, hover, pulsado) in botones.items():
            e.configure(f"{nombre}.TButton", background=bg, foreground="#ffffff",
                        bordercolor=bg, lightcolor=bg, darkcolor=bg, focuscolor=bg,
                        padding=(14, 9), font=(fam, 10, "bold"), relief="flat", borderwidth=0)
            e.map(f"{nombre}.TButton",
                  background=[("disabled", "#262b4d"), ("pressed", pulsado), ("active", hover)],
                  foreground=[("disabled", "#6d7399")],
                  bordercolor=[("disabled", "#262b4d")],
                  lightcolor=[("disabled", "#262b4d")], darkcolor=[("disabled", "#262b4d")])

        e.configure("Valor.TEntry", fieldbackground=PANEL2, foreground=TEXTO, insertcolor=TEXTO,
                    bordercolor=BORDE, lightcolor=BORDE, darkcolor=BORDE, padding=9,
                    selectbackground=ACENTO, selectforeground="#ffffff")
        e.map("Valor.TEntry", bordercolor=[("focus", ACENTO)], lightcolor=[("focus", ACENTO)],
              darkcolor=[("focus", ACENTO)])

        e.configure("Oscuro.TCombobox", fieldbackground=PANEL2, background=PANEL2,
                    foreground=TEXTO, arrowcolor=TEXTO, bordercolor=BORDE, lightcolor=BORDE,
                    darkcolor=BORDE, padding=6, selectbackground=PANEL2, selectforeground=TEXTO)
        e.map("Oscuro.TCombobox", fieldbackground=[("readonly", PANEL2)],
              foreground=[("readonly", TEXTO)], background=[("active", BORDE)])
        self.option_add("*TCombobox*Listbox.background", PANEL2)
        self.option_add("*TCombobox*Listbox.foreground", TEXTO)
        self.option_add("*TCombobox*Listbox.selectBackground", ACENTO)
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

        e.configure("Oscuro.Horizontal.TScale", background=ACENTO, troughcolor=PANEL2,
                    bordercolor=PANEL, lightcolor=ACENTO, darkcolor=ACENTO)
        for orient in ("Vertical", "Horizontal"):
            nombre = f"Oscuro.{orient}.TScrollbar"
            e.configure(nombre, background="#3a4180", troughcolor=LIENZO, bordercolor=LIENZO,
                        arrowcolor=APAGADO, lightcolor="#3a4180", darkcolor="#3a4180", gripcount=0)
            activo = [("active", "#5560b0"), ("!active", "#3a4180")]
            e.map(nombre, background=activo, lightcolor=activo, darkcolor=activo)

    # ==================================================================
    # Construcción de la interfaz
    # ==================================================================
    def _crear_widgets(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self._crear_encabezado()
        self._crear_panel_operaciones()
        self._crear_area_central()
        self._crear_panel_info()
        self._crear_barra_estado()

    @staticmethod
    def _barra_auto(barra: ttk.Scrollbar):
        """Devuelve un ``scrollcommand`` que oculta la barra cuando no hace falta."""
        def actualizar(inicio, fin):
            if float(inicio) <= 0.0 and float(fin) >= 0.999:
                barra.grid_remove()
            else:
                barra.grid()
            barra.set(inicio, fin)
        return actualizar

    def _etiqueta_seccion(self, padre: tk.Widget, texto: str, fondo: str = PANEL) -> None:
        tk.Label(padre, text=texto.upper(), bg=fondo, fg=APAGADO,
                 font=(self.fam, 9, "bold")).pack(anchor="w", pady=(10, 4))

    def _boton(self, padre, texto, estilo, comando, **pack) -> ttk.Button:
        b = ttk.Button(padre, text=texto, style=f"{estilo}.TButton", command=comando,
                       cursor="hand2", takefocus=False)
        b.pack(**({"fill": "x", "pady": 4} | pack))
        self._botones.append(b)
        return b

    # ---------------------------------------------------------------- encabezado
    def _crear_encabezado(self) -> None:
        f = tk.Frame(self, bg=BG)
        f.grid(row=0, column=0, columnspan=3, sticky="ew", padx=20, pady=(10, 6))
        tk.Label(f, text="🌳  Árbol Binario de Búsqueda", bg=BG, fg=TEXTO,
                 font=(self.fam, 19, "bold")).pack(side="left")
        tk.Label(f, text="Estructuras de datos · clases Nodo y Árbol en Python + Tkinter",
                 bg=BG, fg=APAGADO, font=(self.fam, 10)).pack(side="left", padx=16, pady=(8, 0))

    # ---------------------------------------------------------------- A. operaciones
    def _crear_panel_operaciones(self) -> None:
        cont = tk.Frame(self, bg=PANEL, width=250)
        cont.grid(row=1, column=0, sticky="ns", padx=(16, 8), pady=(0, 8))
        cont.pack_propagate(False)
        f = tk.Frame(cont, bg=PANEL)
        f.pack(fill="both", expand=True, padx=18, pady=(6, 16))

        self._etiqueta_seccion(f, "Operaciones")
        tk.Label(f, text="Valor (número entero)", bg=PANEL, fg=TEXTO,
                 font=(self.fam, 10)).pack(anchor="w", pady=(0, 5))
        self.entrada = ttk.Entry(f, textvariable=self.var_valor, style="Valor.TEntry",
                                 font=(self.fam, 14, "bold"), justify="center")
        self.entrada.pack(fill="x", pady=(0, 10))
        self.entrada.bind("<Return>", lambda _e: self.accion_insertar())

        self._boton(f, "＋  Insertar", "Acento", self.accion_insertar)
        self._boton(f, "⌕  Buscar", "Info", self.accion_buscar)
        self._boton(f, "✕  Eliminar", "Peligro", self.accion_eliminar)

        self._etiqueta_seccion(f, "Árbol")
        self._boton(f, "✦  Árbol de ejemplo", "Neutro", self.accion_ejemplo)
        self._boton(f, "⇄  Aleatorizar árbol", "Neutro", self.accion_aleatorio)
        self._boton(f, "⟲  Limpiar árbol", "Neutro", self.accion_limpiar)

        tk.Label(f, text="Sugerencia: pulsa Enter para insertar y haz clic en un nodo "
                         "para copiar su valor al campo.", bg=PANEL, fg=APAGADO, justify="left",
                 wraplength=205, font=(self.fam, 9)).pack(side="bottom", anchor="w")

    # ---------------------------------------------------------------- B. área central
    def _crear_area_central(self) -> None:
        f = tk.Frame(self, bg=BG)
        f.grid(row=1, column=1, sticky="nsew", padx=8, pady=(0, 8))
        f.rowconfigure(1, weight=1)
        f.columnconfigure(0, weight=1)

        tk.Label(f, text="VISUALIZACIÓN DEL ÁRBOL", bg=BG, fg=APAGADO,
                 font=(self.fam, 9, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 6))

        marco = tk.Frame(f, bg=LIENZO, highlightbackground=BORDE, highlightthickness=1)
        marco.grid(row=1, column=0, sticky="nsew")
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(marco, bg=LIENZO, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        sy = ttk.Scrollbar(marco, orient="vertical", command=self.canvas.yview,
                           style="Oscuro.Vertical.TScrollbar")
        sx = ttk.Scrollbar(marco, orient="horizontal", command=self.canvas.xview,
                           style="Oscuro.Horizontal.TScrollbar")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(xscrollcommand=self._barra_auto(sx), yscrollcommand=self._barra_auto(sy))
        self.canvas.bind("<Configure>", self._al_redimensionar)

        # leyenda
        leyenda = tk.Frame(f, bg=BG)
        leyenda.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        for clave, texto in (("raiz", "Raíz"), ("interno", "Interno"), ("hoja", "Hoja"),
                             ("visita", "Visita"), ("encontrado", "Hallado"),
                             ("error", "Error")):
            tk.Label(leyenda, text="●", bg=BG, fg=ESTILOS[clave][0],
                     font=(self.fam, 13)).pack(side="left")
            tk.Label(leyenda, text=texto, bg=BG, fg=APAGADO,
                     font=(self.fam, 9)).pack(side="left", padx=(2, 10))

        # resultados de recorridos
        self._crear_resultados_recorridos(f)

    def _crear_resultados_recorridos(self, padre: tk.Widget) -> None:
        caja = tk.Frame(padre, bg=PANEL, padx=14, pady=10)
        caja.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        caja.columnconfigure(1, weight=1)
        tk.Label(caja, text="RESULTADOS DE LOS RECORRIDOS", bg=PANEL, fg=APAGADO,
                 font=(self.fam, 9, "bold")).grid(row=0, column=0, columnspan=2, sticky="w",
                                                  pady=(0, 6))
        self._etiquetas_resultado = []
        for fila, (clave, (nombre, formula)) in enumerate(RECORRIDOS.items(), start=1):
            tk.Label(caja, text=f"{nombre}", bg=PANEL, fg=TEXTO, anchor="w",
                     font=(self.fam, 10, "bold")).grid(row=fila, column=0, sticky="nw",
                                                       padx=(0, 14), pady=2)
            lb = tk.Label(caja, textvariable=self.var_recorrido[clave], bg=PANEL, fg=INFO,
                          anchor="w", justify="left", font=(self.fam, 10))
            lb.grid(row=fila, column=1, sticky="ew", pady=2)
            self._etiquetas_resultado.append(lb)
        caja.bind("<Configure>", lambda e: [lb.configure(wraplength=max(200, e.width - 140))
                                            for lb in self._etiquetas_resultado])

    # ---------------------------------------------------------------- C. información
    def _crear_panel_info(self) -> None:
        cont = tk.Frame(self, bg=PANEL, width=320)
        cont.grid(row=1, column=2, sticky="ns", padx=(8, 16), pady=(0, 8))
        cont.pack_propagate(False)
        f = tk.Frame(cont, bg=PANEL)
        f.pack(fill="both", expand=True, padx=18, pady=(6, 16))

        self._etiqueta_seccion(f, "Estadísticas")
        rejilla = tk.Frame(f, bg=PANEL)
        rejilla.pack(fill="x")
        rejilla.columnconfigure((0, 1), weight=1, uniform="tarjeta")
        tarjetas = [("Nodos", "nodos"), ("Altura (niveles)", "altura"), ("Hojas", "hojas"),
                    ("Raíz", "raiz"), ("Mínimo", "minimo"), ("Máximo", "maximo")]
        for i, (titulo, clave) in enumerate(tarjetas):
            t = tk.Frame(rejilla, bg=PANEL2, padx=12, pady=4)
            t.grid(row=i // 2, column=i % 2, sticky="ew", padx=3, pady=3)
            tk.Label(t, text=titulo.upper(), bg=PANEL2, fg=APAGADO,
                     font=(self.fam, 8, "bold")).pack(anchor="w")
            tk.Label(t, textvariable=self.var_stats[clave], bg=PANEL2, fg=TEXTO,
                     font=(self.fam, 15, "bold")).pack(anchor="w")

        self._etiqueta_seccion(f, "Estado actual")
        tk.Label(f, textvariable=self.var_estado_arbol, bg=PANEL2, fg=TEXTO, anchor="w",
                 justify="left", wraplength=250, padx=12, pady=6,
                 font=(self.fam, 10)).pack(fill="x")

        self._etiqueta_seccion(f, "Recorridos")
        cuadro = tk.Frame(f, bg=PANEL)
        cuadro.pack(fill="x")
        cuadro.columnconfigure((0, 1), weight=1, uniform="rec")
        for i, (clave, (nombre, formula)) in enumerate(RECORRIDOS.items()):
            b = ttk.Button(cuadro, text=nombre, style="Neutro.TButton", cursor="hand2",
                           takefocus=False, command=lambda k=clave: self.accion_recorrido(k))
            b.grid(row=i // 2, column=i % 2, sticky="ew", padx=3, pady=3)
            self._botones.append(b)

        self._etiqueta_seccion(f, "Recorrido paso a paso")
        self.combo = ttk.Combobox(f, state="readonly", style="Oscuro.TCombobox",
                                  values=[v[0] for v in RECORRIDOS.values()])
        self.combo.current(0)
        self.combo.pack(fill="x", pady=(0, 6))
        self._boton(f, "▶  Animar recorrido", "Exito", self.accion_animar_recorrido)

        fila_vel = tk.Frame(f, bg=PANEL)
        fila_vel.pack(fill="x", pady=(8, 0))
        tk.Label(fila_vel, text="Velocidad", bg=PANEL, fg=APAGADO,
                 font=(self.fam, 9)).pack(side="left")
        ttk.Scale(fila_vel, from_=1, to=5, variable=self.var_velocidad,
                  style="Oscuro.Horizontal.TScale").pack(side="left", fill="x", expand=True,
                                                          padx=(10, 0))

    # ---------------------------------------------------------------- barra de estado
    def _crear_barra_estado(self) -> None:
        f = tk.Frame(self, bg=PANEL)
        f.grid(row=2, column=0, columnspan=3, sticky="ew")
        self._punto = tk.Label(f, text="●", bg=PANEL, fg=INFO, font=(self.fam, 11))
        self._punto.pack(side="left", padx=(16, 6), pady=7)
        tk.Label(f, textvariable=self.var_mensaje, bg=PANEL, fg=TEXTO, anchor="w",
                 font=(self.fam, 10)).pack(side="left", fill="x", expand=True)

    # ==================================================================
    # Utilidades internas
    # ==================================================================
    def _mostrar_estado(self, texto: str, tipo: str = "info") -> None:
        self.var_mensaje.set(texto)
        self._punto.configure(fg=COLORES_ESTADO.get(tipo, INFO))

    def _retardo(self) -> int:
        return RETARDOS[int(round(float(self.var_velocidad.get())))]

    def _bloquear(self, bloquear: bool) -> None:
        self._ocupado = bloquear
        for b in self._botones:
            b.state(["disabled"] if bloquear else ["!disabled"])

    def _programar(self, ms: int, funcion) -> None:
        """``after`` con protección: si falla un paso, se desbloquea la interfaz."""
        def ejecutar():
            try:
                funcion()
            except Exception as exc:                 # noqa: BLE001
                self._bloquear(False)
                self.vis.limpiar_efectos()
                self.vis.dibujar()
                self._mostrar_estado(f"Error inesperado: {exc}", "error")
        self.after(ms, ejecutar)

    def _limpiar_visual(self) -> None:
        """Quita resaltados e insignias y invalida limpiezas pendientes."""
        self._generacion += 1
        self.vis.limpiar_efectos()

    def _limpiar_despues(self, ms: int) -> None:
        """Quita los resaltados dentro de ``ms`` si nadie los cambió mientras tanto."""
        generacion = self._generacion

        def limpiar():
            if generacion == self._generacion and not self._ocupado:
                self._limpiar_visual()
                self.vis.dibujar()
        self.after(ms, limpiar)

    def _refrescar(self) -> None:
        """Redibuja el árbol, actualiza estadísticas y reinicia resultados de recorridos."""
        self.vis.dibujar(self.arbol)
        self.actualizar_estadisticas()
        for v in self.var_recorrido.values():
            v.set("—")

    def actualizar_estadisticas(self) -> None:
        a = self.arbol
        n = a.contar_nodos()
        raiz = a.obtener_raiz()
        vacio = "—"
        self.var_stats["nodos"].set(str(n))
        self.var_stats["altura"].set(str(a.altura()))
        self.var_stats["hojas"].set(str(a.contar_hojas()))
        self.var_stats["raiz"].set(str(raiz.dato) if raiz else vacio)
        minimo, maximo = a.encontrar_minimo(), a.encontrar_maximo()
        self.var_stats["minimo"].set(vacio if minimo is None else str(minimo))
        self.var_stats["maximo"].set(vacio if maximo is None else str(maximo))
        if a.esta_vacio():
            self.var_estado_arbol.set("Árbol vacío. Inserta un valor para comenzar.")
        elif n == 1:
            self.var_estado_arbol.set("Árbol con un único nodo (la raíz, que también es hoja).")
        else:
            self.var_estado_arbol.set(f"Árbol con {n} nodos y {a.altura()} niveles. "
                                      "Cumple el orden de un ABB.")

    @staticmethod
    def _nivel(nodo) -> int:
        nivel = 1
        while nodo.padre is not None:
            nodo = nodo.padre
            nivel += 1
        return nivel

    def _leer_valor(self):
        """Valida el campo de texto. Devuelve un ``int`` o ``None`` (tras avisar)."""
        texto = self.var_valor.get().strip()
        if not texto:
            self._mostrar_estado("El campo está vacío.", "warning")
            messagebox.showwarning("Campo vacío", "Escribe un número entero en el campo de valor.")
            self.entrada.focus_set()
            return None
        try:
            valor = int(texto)
        except ValueError:
            self._mostrar_estado(f"«{texto}» no es un número entero válido.", "warning")
            messagebox.showerror("Dato no válido",
                                 f"«{texto}» no es un número entero.\n\nEjemplos válidos: 42, -7, 100.")
            self.entrada.focus_set()
            self.entrada.selection_range(0, "end")
            return None
        if abs(valor) > VALOR_MAX:
            self._mostrar_estado(f"El valor debe estar entre -{VALOR_MAX} y {VALOR_MAX}.", "warning")
            messagebox.showwarning("Valor fuera de rango",
                                   f"Usa valores entre -{VALOR_MAX} y {VALOR_MAX} "
                                   "para que quepan dentro del nodo.")
            return None
        return valor

    def _aviso_arbol_vacio(self, accion: str) -> None:
        self._mostrar_estado(f"El árbol está vacío: no hay nada que {accion}.", "warning")
        messagebox.showinfo("Árbol vacío", f"El árbol está vacío, no hay nada que {accion}.\n"
                                           "Inserta algunos valores primero.")

    def _animar_camino(self, camino, al_terminar) -> None:
        """Resalta uno a uno los nodos de ``camino`` y luego llama a ``al_terminar``."""
        def paso(i: int) -> None:
            if i < len(camino):
                if i > 0:
                    self.vis.resaltar(camino[i - 1], "camino")
                self.vis.resaltar(camino[i], "visita")
                self.vis.dibujar()
                self._programar(self._retardo(), lambda: paso(i + 1))
            else:
                al_terminar()
        paso(0)

    def _al_clic_nodo(self, nodo) -> None:
        if self._ocupado:
            return
        self.var_valor.set(str(nodo.dato))
        self._mostrar_estado(f"Valor {nodo.dato} copiado al campo · {nodo}", "info")

    def _al_redimensionar(self, _evento) -> None:
        if self._id_redibujo is not None:
            self.after_cancel(self._id_redibujo)
        self._id_redibujo = self.after(30, lambda: self.vis.dibujar())

    # ==================================================================
    # Acciones: insertar / buscar / eliminar
    # ==================================================================
    def accion_insertar(self) -> None:
        if self._ocupado:
            return
        self._limpiar_visual()
        self.vis.dibujar()
        valor = self._leer_valor()
        if valor is None:
            return

        existente = self.arbol.buscar(valor)
        if existente is not None:                     # duplicado
            self.vis.resaltar(existente, "error")
            self.vis.dibujar()
            self._mostrar_estado(f"El valor {valor} ya existe: no se permiten duplicados.", "warning")
            messagebox.showwarning("Valor duplicado",
                                   f"El valor {valor} ya está en el árbol.\n"
                                   "Este ABB no admite elementos duplicados.")
            self._limpiar_visual()
            self.vis.dibujar()
            return

        camino = self.arbol.camino_busqueda(valor)
        self._bloquear(True)
        self._mostrar_estado(f"Insertando {valor}: se compara con {len(camino)} nodo(s)…", "info")

        def colocar() -> None:
            self.arbol.insertar(valor)                # operación real del árbol
            nuevo = self.arbol.buscar(valor)
            self.vis.quitar_resaltados()
            self.vis.establecer_escala(nuevo, 0.05)
            self.vis.resaltar(nuevo, "nuevo")
            self._refrescar()
            self.vis.animar_aparicion(nuevo, lambda: terminar(nuevo))

        def terminar(nuevo) -> None:
            padre = nuevo.padre
            if padre is None:
                donde = "como raíz del árbol"
            else:
                lado = "izquierdo" if padre.izquierdo is nuevo else "derecho"
                donde = f"como hijo {lado} de {padre.dato} (nivel {self._nivel(nuevo)})"
            self._mostrar_estado(f"Valor {valor} insertado {donde}.", "success")
            self.var_valor.set("")
            self._bloquear(False)
            self.entrada.focus_set()
            self._limpiar_despues(1600)

        self._animar_camino(camino, colocar)

    def accion_buscar(self) -> None:
        if self._ocupado:
            return
        self._limpiar_visual()
        self.vis.dibujar()
        valor = self._leer_valor()
        if valor is None:
            return
        if self.arbol.esta_vacio():
            self._aviso_arbol_vacio("buscar")
            return

        camino = self.arbol.camino_busqueda(valor)
        self._bloquear(True)
        self._mostrar_estado(f"Buscando {valor}…", "info")

        def resultado() -> None:
            ultimo = camino[-1]
            if ultimo.dato == valor:
                self.vis.resaltar(ultimo, "encontrado")
                self.vis.dibujar()
                self._mostrar_estado(f"Valor {valor} encontrado en el nivel {self._nivel(ultimo)} "
                                     f"({len(camino)} comparación(es)).", "success")
                self._bloquear(False)
                self._limpiar_despues(2600)
            else:
                self.vis.resaltar(ultimo, "error")
                self.vis.dibujar()
                self._mostrar_estado(f"El valor {valor} no existe en el árbol.", "warning")
                self._bloquear(False)
                messagebox.showinfo("No encontrado",
                                    f"El valor {valor} no existe en el árbol.\n"
                                    f"Se revisaron {len(camino)} nodo(s) antes de llegar a un espacio vacío.")
                self._limpiar_visual()
                self.vis.dibujar()

        self._animar_camino(camino, resultado)

    def accion_eliminar(self) -> None:
        if self._ocupado:
            return
        self._limpiar_visual()
        self.vis.dibujar()
        valor = self._leer_valor()
        if valor is None:
            return
        if self.arbol.esta_vacio():
            self._aviso_arbol_vacio("eliminar")
            return

        camino = self.arbol.camino_busqueda(valor)
        existe = camino[-1].dato == valor
        self._bloquear(True)
        self._mostrar_estado(f"Buscando {valor} para eliminarlo…", "info")

        def resultado() -> None:
            if not existe:
                self.vis.resaltar(camino[-1], "error")
                self.vis.dibujar()
                self._mostrar_estado(f"No se puede eliminar: {valor} no existe en el árbol.", "warning")
                self._bloquear(False)
                messagebox.showinfo("No encontrado",
                                    f"No se puede eliminar el valor {valor} porque no existe en el árbol.")
                self._limpiar_visual()
                self.vis.dibujar()
                return
            nodo = camino[-1]
            caso = self.arbol.caso_eliminacion(valor)
            sucesor = None
            self.vis.resaltar(nodo, "eliminar")
            if caso == "dos_hijos":
                sucesor = self.arbol.sucesor_inorden(valor)
                self.vis.resaltar(sucesor, "sucesor")
            self.vis.dibujar()
            self._mostrar_estado(f"Eliminando {valor} (caso: {self._texto_caso(caso)})…", "warning")
            self._programar(self._retardo() * 2, lambda: confirmar(nodo, caso, sucesor))

        def confirmar(nodo, caso, sucesor) -> None:
            valor_sucesor = sucesor.dato if sucesor is not None else None
            self.arbol.eliminar(valor)                # operación real del árbol
            self.vis.quitar_resaltados()
            if caso == "dos_hijos":
                self.vis.resaltar(nodo, "sucesor")    # este nodo ahora guarda el sucesor
            self._refrescar()
            detalle = {
                "hoja": "era un nodo hoja y simplemente se desconectó.",
                "un_hijo": "tenía un hijo, que ocupó su lugar.",
                "dos_hijos": f"tenía dos hijos: lo reemplazó su sucesor inorden ({valor_sucesor}).",
            }[caso]
            self._mostrar_estado(f"Valor {valor} eliminado: {detalle}", "success")
            self.var_valor.set("")
            self._bloquear(False)
            self.entrada.focus_set()
            self._limpiar_despues(1800)

        self._animar_camino(camino, resultado)

    @staticmethod
    def _texto_caso(caso: str) -> str:
        return {"hoja": "nodo hoja", "un_hijo": "un hijo", "dos_hijos": "dos hijos"}[caso]

    # ==================================================================
    # Acciones: generar / aleatorizar / limpiar
    # ==================================================================
    def _cargar(self, valores, mensaje: str) -> None:
        self._limpiar_visual()
        self.arbol.limpiar()
        for v in valores:
            self.arbol.insertar(v)
        self._refrescar()
        self._mostrar_estado(mensaje, "success")

    def accion_ejemplo(self) -> None:
        if self._ocupado:
            return
        self._cargar(EJEMPLO, f"Árbol de ejemplo generado con {len(EJEMPLO)} nodos "
                              f"(orden de inserción: {', '.join(map(str, EJEMPLO))}).")

    def accion_aleatorio(self) -> None:
        if self._ocupado:
            return
        cantidad = random.randint(8, 15)
        valores = random.sample(range(1, 100), cantidad)
        self._cargar(valores, f"Árbol aleatorio generado con {cantidad} valores distintos.")

    def accion_limpiar(self) -> None:
        if self._ocupado:
            return
        if self.arbol.esta_vacio():
            self._aviso_arbol_vacio("limpiar")
            return
        n = self.arbol.contar_nodos()
        if not messagebox.askyesno("Limpiar árbol",
                                   f"Se eliminarán los {n} nodos del árbol.\n¿Deseas continuar?"):
            return
        self._limpiar_visual()
        self.arbol.limpiar()
        self._refrescar()
        self._mostrar_estado("Árbol limpiado. Ya puedes insertar nuevos valores.", "success")

    # ==================================================================
    # Recorridos
    # ==================================================================
    def _recorrido(self, clave: str, nodos: bool = False) -> list:
        funcion = {
            "preorden": self.arbol.recorrido_preorden,
            "inorden": self.arbol.recorrido_inorden,
            "postorden": self.arbol.recorrido_postorden,
            "niveles": self.arbol.recorrido_por_niveles,
        }[clave]
        return funcion(nodos=nodos)

    def accion_recorrido(self, clave: str) -> None:
        if self._ocupado:
            return
        self._limpiar_visual()
        self.vis.dibujar()
        if self.arbol.esta_vacio():
            self._aviso_arbol_vacio("recorrer")
            return
        datos = self._recorrido(clave)
        self.var_recorrido[clave].set(" → ".join(map(str, datos)))
        nombre, formula = RECORRIDOS[clave]
        self._mostrar_estado(f"Recorrido {nombre.lower()} ({formula}): {len(datos)} nodos visitados.",
                             "success")

    def accion_animar_recorrido(self) -> None:
        if self._ocupado:
            return
        self._limpiar_visual()
        self.vis.dibujar()
        if self.arbol.esta_vacio():
            self._aviso_arbol_vacio("recorrer")
            return
        clave = list(RECORRIDOS)[self.combo.current()]
        nombre = RECORRIDOS[clave][0]
        nodos = self._recorrido(clave, nodos=True)
        visitados: list = []
        self._bloquear(True)

        def paso(i: int) -> None:
            if i > 0:
                self.vis.resaltar(nodos[i - 1], "camino")
            if i < len(nodos):
                actual = nodos[i]
                self.vis.resaltar(actual, "visita")
                self.vis.etiquetar(actual, str(i + 1))
                visitados.append(actual.dato)
                self.var_recorrido[clave].set(" → ".join(map(str, visitados)))
                self._mostrar_estado(f"{nombre}: visitando el nodo {actual.dato} "
                                     f"(paso {i + 1} de {len(nodos)})", "info")
                self.vis.dibujar()
                self._programar(self._retardo(), lambda: paso(i + 1))
            else:
                self._mostrar_estado(f"Recorrido {nombre.lower()} completado: "
                                     f"{len(nodos)} nodos visitados.", "success")
                self._bloquear(False)

        paso(0)
