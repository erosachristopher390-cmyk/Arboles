"""
nodo.py
=======
Implementación de la clase ``Nodo`` utilizada por el árbol binario de búsqueda.

Cada nodo guarda un dato y mantiene tres referencias:

* ``izquierdo``: hijo izquierdo (valores menores).
* ``derecho``:   hijo derecho (valores mayores).
* ``padre``:     nodo padre (``None`` en la raíz). Facilita la eliminación
  y permite calcular el nivel de un nodo sin recorrer todo el árbol.
"""

from __future__ import annotations

from typing import List, Optional


class Nodo:
    """Elemento básico de un árbol binario."""

    __slots__ = ("dato", "izquierdo", "derecho", "padre")

    def __init__(self, dato: int, padre: Optional["Nodo"] = None) -> None:
        """Inicializa un nodo sin hijos.

        :param dato: valor que almacenará el nodo.
        :param padre: nodo padre (``None`` si el nodo será la raíz).
        """
        self.dato = dato
        self.izquierdo: Optional[Nodo] = None
        self.derecho: Optional[Nodo] = None
        self.padre: Optional[Nodo] = padre

    # ------------------------------------------------------------------
    # Asignación de hijos
    # ------------------------------------------------------------------
    def asignar_izquierdo(self, nodo: Optional["Nodo"]) -> None:
        """Asigna el hijo izquierdo y actualiza el padre del hijo."""
        self.izquierdo = nodo
        if nodo is not None:
            nodo.padre = self

    def asignar_derecho(self, nodo: Optional["Nodo"]) -> None:
        """Asigna el hijo derecho y actualiza el padre del hijo."""
        self.derecho = nodo
        if nodo is not None:
            nodo.padre = self

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def es_hoja(self) -> bool:
        """``True`` si el nodo no tiene ningún hijo."""
        return self.izquierdo is None and self.derecho is None

    def tiene_hijos(self) -> bool:
        """``True`` si el nodo tiene al menos un hijo."""
        return not self.es_hoja()

    def numero_hijos(self) -> int:
        """Grado del nodo: 0, 1 o 2 hijos."""
        return (self.izquierdo is not None) + (self.derecho is not None)

    def es_raiz(self) -> bool:
        """``True`` si el nodo no tiene padre."""
        return self.padre is None

    def hijos(self) -> List["Nodo"]:
        """Lista de hijos existentes (izquierdo primero)."""
        return [h for h in (self.izquierdo, self.derecho) if h is not None]

    def tipo(self) -> str:
        """Clasificación del nodo: ``'raíz'``, ``'interno'`` u ``'hoja'``."""
        if self.es_raiz():
            return "raíz"
        return "hoja" if self.es_hoja() else "interno"

    # ------------------------------------------------------------------
    # Información
    # ------------------------------------------------------------------
    def obtener_info(self) -> dict:
        """Devuelve un diccionario con la información del nodo."""
        return {
            "dato": self.dato,
            "tipo": self.tipo(),
            "grado": self.numero_hijos(),
            "padre": self.padre.dato if self.padre else None,
            "izquierdo": self.izquierdo.dato if self.izquierdo else None,
            "derecho": self.derecho.dato if self.derecho else None,
        }

    def __str__(self) -> str:
        info = self.obtener_info()
        return (
            f"Nodo({info['dato']}) · {info['tipo']} · padre={info['padre']} · "
            f"izq={info['izquierdo']} · der={info['derecho']}"
        )

    def __repr__(self) -> str:
        return f"Nodo({self.dato!r})"
