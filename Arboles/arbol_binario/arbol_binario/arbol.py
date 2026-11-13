"""
arbol.py
========
Implementación de la clase ``Arbol``: un **árbol binario de búsqueda (ABB)**.

Reglas del ABB
--------------
* Los valores *menores* que un nodo van en su subárbol izquierdo.
* Los valores *mayores* van en su subárbol derecho.
* **No se permiten duplicados**: ``insertar`` devuelve ``False`` si el valor
  ya existe y el árbol no cambia.

Convenciones (tomadas de la presentación de clase)
--------------------------------------------------
* El nivel de la raíz es 1 y un árbol vacío tiene 0 niveles.
* La **altura** es el número máximo de niveles del árbol.

Todos los algoritmos son *iterativos*; así un árbol degenerado (por ejemplo,
al insertar valores ordenados) no provoca ``RecursionError``.
"""

from __future__ import annotations

from collections import deque
from typing import Iterator, List, Optional

from nodo import Nodo


class Arbol:
    """Árbol binario de búsqueda de números enteros."""

    def __init__(self) -> None:
        self._raiz: Optional[Nodo] = None

    # ------------------------------------------------------------------
    # Consultas básicas
    # ------------------------------------------------------------------
    def obtener_raiz(self) -> Optional[Nodo]:
        """Devuelve el nodo raíz (``None`` si el árbol está vacío)."""
        return self._raiz

    def esta_vacio(self) -> bool:
        """``True`` si el árbol no contiene nodos."""
        return self._raiz is None

    def limpiar(self) -> None:
        """Elimina todos los elementos del árbol."""
        self._raiz = None

    # ------------------------------------------------------------------
    # Búsqueda
    # ------------------------------------------------------------------
    def buscar(self, dato) -> Optional[Nodo]:
        """Localiza ``dato``. Devuelve su nodo o ``None`` si no existe."""
        actual = self._raiz
        while actual is not None:
            if dato == actual.dato:
                return actual
            actual = actual.izquierdo if dato < actual.dato else actual.derecho
        return None

    def camino_busqueda(self, dato) -> List[Nodo]:
        """Nodos que se visitan al buscar ``dato`` (desde la raíz).

        Si el dato existe, el último nodo es el que lo contiene; si no, el
        último es aquel donde la búsqueda se detuvo (el futuro padre en una
        inserción). Se usa para animar búsquedas, inserciones y eliminaciones.
        """
        camino: List[Nodo] = []
        actual = self._raiz
        while actual is not None:
            camino.append(actual)
            if dato == actual.dato:
                break
            actual = actual.izquierdo if dato < actual.dato else actual.derecho
        return camino

    # ------------------------------------------------------------------
    # Inserción
    # ------------------------------------------------------------------
    def insertar(self, dato) -> bool:
        """Inserta ``dato`` respetando el orden del ABB.

        :return: ``True`` si se insertó; ``False`` si el valor ya existía.
        """
        if self._raiz is None:
            self._raiz = Nodo(dato)
            return True

        actual = self._raiz
        while True:
            if dato == actual.dato:
                return False                      # duplicado: se rechaza
            if dato < actual.dato:
                if actual.izquierdo is None:
                    actual.asignar_izquierdo(Nodo(dato))
                    return True
                actual = actual.izquierdo
            else:
                if actual.derecho is None:
                    actual.asignar_derecho(Nodo(dato))
                    return True
                actual = actual.derecho

    # ------------------------------------------------------------------
    # Eliminación
    # ------------------------------------------------------------------
    def caso_eliminacion(self, dato) -> Optional[str]:
        """Indica qué caso de eliminación aplica a ``dato``.

        :return: ``'hoja'``, ``'un_hijo'``, ``'dos_hijos'`` o ``None`` si el
                 dato no existe.
        """
        nodo = self.buscar(dato)
        if nodo is None:
            return None
        return {0: "hoja", 1: "un_hijo", 2: "dos_hijos"}[nodo.numero_hijos()]

    def sucesor_inorden(self, dato) -> Optional[Nodo]:
        """Sucesor inorden de un nodo con dos hijos: el mínimo de su subárbol
        derecho. Devuelve ``None`` si el dato no existe o no tiene hijo derecho.
        """
        nodo = self.buscar(dato)
        if nodo is None or nodo.derecho is None:
            return None
        return self._minimo_desde(nodo.derecho)

    def eliminar(self, dato) -> bool:
        """Elimina ``dato`` conservando las propiedades del ABB.

        Casos:
          1. Hoja: se desconecta del padre.
          2. Un hijo: el hijo ocupa el lugar del nodo eliminado.
          3. Dos hijos: el nodo toma el valor de su sucesor inorden y se
             elimina el sucesor (que tiene a lo sumo un hijo).

        :return: ``True`` si se eliminó; ``False`` si el dato no existía.
        """
        nodo = self.buscar(dato)
        if nodo is None:
            return False

        if nodo.izquierdo is not None and nodo.derecho is not None:
            sucesor = self._minimo_desde(nodo.derecho)
            nodo.dato = sucesor.dato
            nodo = sucesor                        # ahora se borra el sucesor

        hijo = nodo.izquierdo if nodo.izquierdo is not None else nodo.derecho
        self._reemplazar(nodo, hijo)
        return True

    def _reemplazar(self, nodo: Nodo, hijo: Optional[Nodo]) -> None:
        """Sustituye ``nodo`` por ``hijo`` (que puede ser ``None``) en su padre."""
        padre = nodo.padre
        if padre is None:
            self._raiz = hijo
            if hijo is not None:
                hijo.padre = None
        elif padre.izquierdo is nodo:
            padre.asignar_izquierdo(hijo)
        else:
            padre.asignar_derecho(hijo)
        nodo.padre = nodo.izquierdo = nodo.derecho = None   # nodo desconectado

    # ------------------------------------------------------------------
    # Mínimo y máximo
    # ------------------------------------------------------------------
    @staticmethod
    def _minimo_desde(nodo: Nodo) -> Nodo:
        while nodo.izquierdo is not None:
            nodo = nodo.izquierdo
        return nodo

    @staticmethod
    def _maximo_desde(nodo: Nodo) -> Nodo:
        while nodo.derecho is not None:
            nodo = nodo.derecho
        return nodo

    def encontrar_minimo(self):
        """Menor valor del árbol (``None`` si está vacío)."""
        return None if self._raiz is None else self._minimo_desde(self._raiz).dato

    def encontrar_maximo(self):
        """Mayor valor del árbol (``None`` si está vacío)."""
        return None if self._raiz is None else self._maximo_desde(self._raiz).dato

    # ------------------------------------------------------------------
    # Medidas del árbol
    # ------------------------------------------------------------------
    def altura(self) -> int:
        """Número máximo de niveles (raíz = nivel 1; árbol vacío = 0)."""
        if self._raiz is None:
            return 0
        nivel = [self._raiz]
        altura = 0
        while nivel:
            altura += 1
            nivel = [h for n in nivel for h in n.hijos()]
        return altura

    def contar_nodos(self) -> int:
        """Número total de nodos (el «peso» del árbol)."""
        return len(self._preorden_nodos())

    def contar_hojas(self) -> int:
        """Número de nodos sin hijos."""
        return sum(1 for n in self._preorden_nodos() if n.es_hoja())

    # ------------------------------------------------------------------
    # Recorridos (iterativos). Con ``nodos=True`` devuelven objetos Nodo,
    # lo que permite animar el recorrido paso a paso.
    # ------------------------------------------------------------------
    def _preorden_nodos(self) -> List[Nodo]:
        resultado: List[Nodo] = []
        pila = [self._raiz] if self._raiz is not None else []
        while pila:
            nodo = pila.pop()
            resultado.append(nodo)                # raíz
            if nodo.derecho is not None:
                pila.append(nodo.derecho)         # se apila primero la derecha
            if nodo.izquierdo is not None:
                pila.append(nodo.izquierdo)       # para visitar antes la izquierda
        return resultado

    def _inorden_nodos(self) -> List[Nodo]:
        resultado: List[Nodo] = []
        pila: List[Nodo] = []
        actual = self._raiz
        while pila or actual is not None:
            while actual is not None:             # bajar por la izquierda
                pila.append(actual)
                actual = actual.izquierdo
            actual = pila.pop()
            resultado.append(actual)              # raíz entre izquierda y derecha
            actual = actual.derecho
        return resultado

    def _postorden_nodos(self) -> List[Nodo]:
        if self._raiz is None:
            return []
        pila = [self._raiz]
        salida: List[Nodo] = []
        while pila:                               # genera raíz-der-izq ...
            nodo = pila.pop()
            salida.append(nodo)
            if nodo.izquierdo is not None:
                pila.append(nodo.izquierdo)
            if nodo.derecho is not None:
                pila.append(nodo.derecho)
        salida.reverse()                          # ... y se invierte: izq-der-raíz
        return salida

    def _niveles_nodos(self) -> List[Nodo]:
        resultado: List[Nodo] = []
        cola = deque([self._raiz]) if self._raiz is not None else deque()
        while cola:
            nodo = cola.popleft()
            resultado.append(nodo)
            cola.extend(nodo.hijos())
        return resultado

    @staticmethod
    def _salida(lista: List[Nodo], nodos: bool) -> list:
        return lista if nodos else [n.dato for n in lista]

    def recorrido_preorden(self, nodos: bool = False) -> list:
        """Raíz, izquierda, derecha."""
        return self._salida(self._preorden_nodos(), nodos)

    def recorrido_inorden(self, nodos: bool = False) -> list:
        """Izquierda, raíz, derecha (en un ABB devuelve los datos ordenados)."""
        return self._salida(self._inorden_nodos(), nodos)

    def recorrido_postorden(self, nodos: bool = False) -> list:
        """Izquierda, derecha, raíz."""
        return self._salida(self._postorden_nodos(), nodos)

    def recorrido_por_niveles(self, nodos: bool = False) -> list:
        """Recorrido por amplitud (nivel por nivel, de izquierda a derecha)."""
        return self._salida(self._niveles_nodos(), nodos)

    # ------------------------------------------------------------------
    # Métodos especiales de Python (comodidad)
    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return self.contar_nodos()

    def __contains__(self, dato) -> bool:
        return self.buscar(dato) is not None

    def __iter__(self) -> Iterator:
        return iter(self.recorrido_inorden())

    def __repr__(self) -> str:
        return f"Arbol(inorden={self.recorrido_inorden()})"
