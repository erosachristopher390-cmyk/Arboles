"""
visualizador.py
===============
Dibujo y distribución gráfica del árbol sobre un ``tkinter.Canvas``.

Distribución de los nodos
-------------------------
* **Eje X**: cada nodo ocupa una columna propia, igual a su posición en el
  recorrido *inorden*. Como el inorden asigna una columna distinta a cada
  nodo, **ningún nodo puede encimarse** con otro. Además, en un ABB el orden
  horizontal coincide con el orden de los valores.
* **Eje Y**: el nivel (profundidad) del nodo.
* El espaciado y el radio se adaptan al tamaño del canvas. Si el árbol es más
  grande que la ventana, se activa el desplazamiento (scrollbars) en lugar de
  encimar los nodos.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, Dict, Optional, Tuple

# ----------------------------------------------------------------------
# Estilos: nombre -> (color de relleno, color de borde)
# ----------------------------------------------------------------------
ESTILOS: Dict[str, Tuple[str, str]] = {
    "raiz":       ("#6c63ff", "#b3adff"),   # raíz
    "interno":    ("#2d7ff9", "#8dbbff"),   # nodos internos
    "hoja":       ("#1fb98a", "#7ee8c4"),   # hojas
    "camino":     ("#26305c", "#4cc9f0"),   # nodos ya recorridos
    "visita":     ("#ffb454", "#fff0c9"),   # nodo que se está visitando
    "encontrado": ("#ffd84d", "#ffffff"),   # búsqueda exitosa
    "nuevo":      ("#ffd84d", "#ffffff"),   # nodo recién insertado
    "error":      ("#ff5c7a", "#ffc2cd"),   # no existe / duplicado
    "eliminar":   ("#ff5c7a", "#ffc2cd"),   # nodo que se elimina
    "sucesor":    ("#ff8a3d", "#ffd2b0"),   # sucesor inorden
}
_TEXTO_OSCURO = {"visita", "encontrado", "nuevo"}


def _limitar(valor: float, minimo: float, maximo: float) -> float:
    return max(minimo, min(maximo, valor))


class Visualizador:
    """Dibuja un ``Arbol`` en un canvas y administra los resaltados."""

    MARGEN_X, MARGEN_SUP, MARGEN_INF = 40, 46, 40
    ESP_X_MIN, ESP_X_MAX = 36, 72
    ESP_Y_MIN, ESP_Y_MAX = 60, 92
    RADIO_MIN, RADIO_MAX = 12, 26

    def __init__(
        self,
        canvas: tk.Canvas,
        color_arista: str = "#4a5188",
        color_vacio: str = "#8a91b4",
        al_clic_nodo: Optional[Callable] = None,
    ) -> None:
        self.canvas = canvas
        self.color_arista = color_arista
        self.color_vacio = color_vacio
        self.al_clic_nodo = al_clic_nodo

        self._arbol = None
        self._resaltados: Dict[int, str] = {}      # id(nodo) -> estilo
        self._etiquetas: Dict[int, str] = {}       # id(nodo) -> texto (orden de visita)
        self._escalas: Dict[int, float] = {}       # id(nodo) -> factor de tamaño
        self._tag_a_nodo: Dict[str, object] = {}
        self._familia = tkfont.nametofont("TkDefaultFont").actual()["family"]

        canvas.tag_bind("nodo", "<Button-1>", self._clic)
        canvas.tag_bind("nodo", "<Enter>", lambda _e: canvas.configure(cursor="hand2"))
        canvas.tag_bind("nodo", "<Leave>", lambda _e: canvas.configure(cursor=""))

    # ------------------------------------------------------------------
    # API de resaltado
    # ------------------------------------------------------------------
    def resaltar(self, nodo, estilo: str) -> None:
        """Aplica un estilo (clave de ``ESTILOS``) a un nodo."""
        if nodo is not None:
            self._resaltados[id(nodo)] = estilo

    def quitar_resaltados(self) -> None:
        self._resaltados.clear()

    def etiquetar(self, nodo, texto: str) -> None:
        """Muestra una pequeña insignia (p. ej. el orden de visita)."""
        if nodo is not None:
            self._etiquetas[id(nodo)] = texto

    def quitar_etiquetas(self) -> None:
        self._etiquetas.clear()

    def establecer_escala(self, nodo, factor: float) -> None:
        self._escalas[id(nodo)] = factor

    def limpiar_efectos(self) -> None:
        """Quita resaltados, insignias y escalas temporales."""
        self._resaltados.clear()
        self._etiquetas.clear()
        self._escalas.clear()

    # ------------------------------------------------------------------
    # Animación de aparición de un nodo nuevo
    # ------------------------------------------------------------------
    def animar_aparicion(
        self, nodo, al_terminar: Optional[Callable] = None, cuadros: int = 9, intervalo: int = 22
    ) -> None:
        """El nodo «crece» desde un punto hasta su tamaño final (con rebote)."""
        clave = id(nodo)

        def facil(f: float) -> float:              # easeOutBack
            c1, c3 = 1.70158, 2.70158
            return 1 + c3 * (f - 1) ** 3 + c1 * (f - 1) ** 2

        def paso(i: int) -> None:
            try:
                if i >= cuadros:
                    self._escalas.pop(clave, None)
                else:
                    self._escalas[clave] = max(0.05, facil(i / cuadros))
                self.dibujar()
                if i < cuadros:
                    self.canvas.after(intervalo, lambda: paso(i + 1))
                elif al_terminar:
                    al_terminar()
            except tk.TclError:                    # ventana cerrada durante la animación
                pass

        paso(0)

    # ------------------------------------------------------------------
    # Distribución
    # ------------------------------------------------------------------
    @staticmethod
    def _posiciones(raiz):
        """Lista de ``(nodo, columna, nivel)`` usando un inorden iterativo."""
        resultado = []
        pila = []
        actual, nivel, columna = raiz, 0, 0
        while pila or actual is not None:
            while actual is not None:
                pila.append((actual, nivel))
                actual = actual.izquierdo
                nivel += 1
            actual, nivel = pila.pop()
            resultado.append((actual, columna, nivel))
            columna += 1
            actual = actual.derecho
            nivel += 1
        return resultado

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def dibujar(self, arbol=None) -> None:
        """Redibuja el árbol completo (si se pasa ``arbol`` se recuerda)."""
        if arbol is not None:
            self._arbol = arbol
        c = self.canvas
        c.delete("all")
        self._tag_a_nodo = {}

        ancho = max(c.winfo_width(), 300)
        alto = max(c.winfo_height(), 200)
        raiz = self._arbol.obtener_raiz() if self._arbol is not None else None

        if raiz is None:
            c.configure(scrollregion=(0, 0, ancho, alto))
            c.create_text(ancho / 2, alto / 2 - 14, text="El árbol está vacío",
                          fill=self.color_vacio, font=(self._familia, 18, "bold"))
            c.create_text(ancho / 2, alto / 2 + 18,
                          text="Inserta un valor o genera un árbol de ejemplo para comenzar",
                          fill=self.color_vacio, font=(self._familia, 11))
            return

        pos = self._posiciones(raiz)
        n = len(pos)
        niveles = max(p[2] for p in pos) + 1

        disponible_x = ancho - 2 * self.MARGEN_X
        esp_x = _limitar(disponible_x / n, self.ESP_X_MIN, self.ESP_X_MAX)
        if niveles > 1:
            esp_y = _limitar((alto - self.MARGEN_SUP - self.MARGEN_INF) / (niveles - 1),
                             self.ESP_Y_MIN, self.ESP_Y_MAX)
        else:
            esp_y = self.ESP_Y_MAX
        radio = _limitar(min(esp_x * 0.44, esp_y * 0.40), self.RADIO_MIN, self.RADIO_MAX)

        contenido_x = 2 * self.MARGEN_X + n * esp_x
        contenido_y = self.MARGEN_SUP + (niveles - 1) * esp_y + self.MARGEN_INF
        desplazamiento = max(0.0, (ancho - contenido_x) / 2)       # centrar si cabe
        c.configure(scrollregion=(0, 0, max(ancho, contenido_x), max(alto, contenido_y)))
        if contenido_x <= ancho:
            c.xview_moveto(0)
        if contenido_y <= alto:
            c.yview_moveto(0)

        coords = {}
        for nodo, col, niv in pos:
            x = desplazamiento + self.MARGEN_X + (col + 0.5) * esp_x
            y = self.MARGEN_SUP + radio * 0.4 + niv * esp_y
            coords[id(nodo)] = (x, y)

        # 1) aristas (debajo de los nodos)
        for nodo, _col, _niv in pos:
            x, y = coords[id(nodo)]
            for hijo in nodo.hijos():
                hx, hy = coords[id(hijo)]
                c.create_line(x, y, hx, hy, fill=self.color_arista, width=2, capstyle="round")

        # 2) nodos
        for indice, (nodo, _col, _niv) in enumerate(pos):
            x, y = coords[id(nodo)]
            estilo = self._resaltados.get(id(nodo))
            destacado = estilo is not None
            if estilo is None:
                estilo = "raiz" if nodo.padre is None else ("hoja" if nodo.es_hoja() else "interno")
            relleno, borde = ESTILOS[estilo]
            r = radio * self._escalas.get(id(nodo), 1.0)
            etiqueta = f"n{indice}"
            self._tag_a_nodo[etiqueta] = nodo

            # halo para nodos resaltados
            if destacado and estilo not in ("camino",):
                c.create_oval(x - r - 5, y - r - 5, x + r + 5, y + r + 5,
                              outline=borde, width=1, dash=(3, 3), tags=("nodo", etiqueta))
            c.create_oval(x - r, y - r, x + r, y + r, fill=relleno, outline=borde,
                          width=3 if destacado else 2, tags=("nodo", etiqueta))

            texto = str(nodo.dato)
            tam = int(_limitar(min(r * 0.72, r * 1.5 / max(len(texto), 1.5)), 7, 20))
            c.create_text(x, y, text=texto, tags=("nodo", etiqueta),
                          fill="#1a1d33" if estilo in _TEXTO_OSCURO else "#ffffff",
                          font=(self._familia, tam, "bold"))

            insignia = self._etiquetas.get(id(nodo))
            if insignia is not None:
                bx, by, br = x + r * 0.85, y - r * 0.85, max(9, r * 0.42)
                c.create_oval(bx - br, by - br, bx + br, by + br, fill="#0f1220",
                              outline="#ffb454", width=2)
                c.create_text(bx, by, text=insignia, fill="#ffb454",
                              font=(self._familia, max(7, int(br * 0.9)), "bold"))

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def _clic(self, _evento) -> None:
        if self.al_clic_nodo is None:
            return
        actuales = self.canvas.find_withtag("current")
        if not actuales:
            return
        for etiqueta in self.canvas.gettags(actuales[0]):
            nodo = self._tag_a_nodo.get(etiqueta)
            if nodo is not None:
                self.al_clic_nodo(nodo)
                return
