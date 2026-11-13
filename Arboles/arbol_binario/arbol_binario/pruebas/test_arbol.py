"""Pruebas unitarias de Nodo y Arbol.   Ejecutar:  python -m unittest discover -s pruebas -v"""
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from arbol import Arbol  # noqa: E402
from nodo import Nodo  # noqa: E402

EJEMPLO = [50, 30, 70, 20, 40, 60, 80, 35, 45, 65]


def construir(valores):
    a = Arbol()
    for v in valores:
        a.insertar(v)
    return a


def es_abb_valido(arbol):
    """Verifica el orden ABB y la coherencia de los punteros ``padre``."""
    def revisar(n, minimo, maximo):
        if n is None:
            return True
        if (minimo is not None and n.dato <= minimo) or (maximo is not None and n.dato >= maximo):
            return False
        for h in n.hijos():
            if h.padre is not n:
                return False
        return revisar(n.izquierdo, minimo, n.dato) and revisar(n.derecho, n.dato, maximo)
    raiz = arbol.obtener_raiz()
    return (raiz is None or raiz.padre is None) and revisar(raiz, None, None)


class PruebasNodo(unittest.TestCase):
    def test_nodo_nuevo_es_hoja(self):
        n = Nodo(5)
        self.assertTrue(n.es_hoja())
        self.assertFalse(n.tiene_hijos())
        self.assertEqual(n.obtener_info()["dato"], 5)

    def test_asignar_hijos_actualiza_padre(self):
        p, i, d = Nodo(10), Nodo(5), Nodo(15)
        p.asignar_izquierdo(i)
        p.asignar_derecho(d)
        self.assertIs(i.padre, p)
        self.assertIs(d.padre, p)
        self.assertTrue(p.tiene_hijos())
        self.assertEqual(p.numero_hijos(), 2)
        self.assertEqual(p.obtener_info()["izquierdo"], 5)


class PruebasArbol(unittest.TestCase):
    def test_arbol_vacio(self):
        a = Arbol()
        self.assertTrue(a.esta_vacio())
        self.assertIsNone(a.obtener_raiz())
        self.assertEqual((a.altura(), a.contar_nodos(), a.contar_hojas()), (0, 0, 0))
        self.assertIsNone(a.encontrar_minimo())
        self.assertIsNone(a.encontrar_maximo())
        self.assertEqual(a.recorrido_inorden(), [])
        self.assertEqual(a.recorrido_por_niveles(), [])
        self.assertFalse(a.eliminar(1))
        self.assertIsNone(a.buscar(1))

    def test_un_solo_nodo(self):
        a = construir([7])
        self.assertEqual((a.altura(), a.contar_nodos(), a.contar_hojas()), (1, 1, 1))
        self.assertEqual((a.encontrar_minimo(), a.encontrar_maximo()), (7, 7))
        self.assertTrue(a.eliminar(7))
        self.assertTrue(a.esta_vacio())

    def test_insertar_y_orden_abb(self):
        a = construir(EJEMPLO)
        self.assertTrue(es_abb_valido(a))
        self.assertEqual(a.recorrido_inorden(), sorted(EJEMPLO))

    def test_duplicados_se_rechazan(self):
        a = construir(EJEMPLO)
        self.assertFalse(a.insertar(40))
        self.assertEqual(a.contar_nodos(), len(EJEMPLO))

    def test_buscar(self):
        a = construir(EJEMPLO)
        self.assertEqual(a.buscar(60).dato, 60)
        self.assertIsNone(a.buscar(99))
        self.assertIn(45, a)
        self.assertNotIn(46, a)

    def test_camino_busqueda(self):
        a = construir(EJEMPLO)
        self.assertEqual([n.dato for n in a.camino_busqueda(45)], [50, 30, 40, 45])
        self.assertEqual([n.dato for n in a.camino_busqueda(66)], [50, 70, 60, 65])

    def test_medidas(self):
        a = construir(EJEMPLO)
        self.assertEqual(a.altura(), 4)
        self.assertEqual(a.contar_nodos(), 10)
        self.assertEqual(a.contar_hojas(), 5)        # 20, 35, 45, 65, 80
        self.assertEqual((a.encontrar_minimo(), a.encontrar_maximo()), (20, 80))

    def test_recorridos(self):
        a = construir(EJEMPLO)
        self.assertEqual(a.recorrido_preorden(), [50, 30, 20, 40, 35, 45, 70, 60, 65, 80])
        self.assertEqual(a.recorrido_inorden(), [20, 30, 35, 40, 45, 50, 60, 65, 70, 80])
        self.assertEqual(a.recorrido_postorden(), [20, 35, 45, 40, 30, 65, 60, 80, 70, 50])
        self.assertEqual(a.recorrido_por_niveles(), [50, 30, 70, 20, 40, 60, 80, 35, 45, 65])

    def test_recorridos_como_nodos(self):
        a = construir(EJEMPLO)
        nodos = a.recorrido_preorden(nodos=True)
        self.assertTrue(all(isinstance(n, Nodo) for n in nodos))
        self.assertEqual([n.dato for n in nodos], a.recorrido_preorden())

    def test_eliminar_hoja(self):
        a = construir(EJEMPLO)
        self.assertEqual(a.caso_eliminacion(80), "hoja")
        self.assertTrue(a.eliminar(80))
        self.assertIsNone(a.buscar(80))
        self.assertEqual(a.contar_nodos(), 9)
        self.assertTrue(es_abb_valido(a))

    def test_eliminar_un_hijo(self):
        a = construir(EJEMPLO)
        self.assertEqual(a.caso_eliminacion(60), "un_hijo")
        self.assertTrue(a.eliminar(60))
        self.assertEqual(a.buscar(70).izquierdo.dato, 65)
        self.assertTrue(es_abb_valido(a))
        self.assertEqual(a.recorrido_inorden(), [20, 30, 35, 40, 45, 50, 65, 70, 80])

    def test_eliminar_dos_hijos(self):
        a = construir(EJEMPLO)
        self.assertEqual(a.caso_eliminacion(30), "dos_hijos")
        self.assertEqual(a.sucesor_inorden(30).dato, 35)
        self.assertTrue(a.eliminar(30))
        self.assertIsNone(a.buscar(30))
        self.assertEqual(a.buscar(50).izquierdo.dato, 35)
        self.assertTrue(es_abb_valido(a))
        self.assertEqual(a.contar_nodos(), 9)

    def test_eliminar_raiz_en_todos_los_casos(self):
        a = construir(EJEMPLO)                       # raíz con dos hijos
        a.eliminar(50)
        self.assertEqual(a.obtener_raiz().dato, 60)
        self.assertTrue(es_abb_valido(a))
        b = construir([10, 5])                       # raíz con un hijo
        b.eliminar(10)
        self.assertEqual(b.obtener_raiz().dato, 5)
        self.assertIsNone(b.obtener_raiz().padre)
        self.assertTrue(es_abb_valido(b))

    def test_eliminar_inexistente(self):
        a = construir(EJEMPLO)
        self.assertFalse(a.eliminar(1234))
        self.assertEqual(a.contar_nodos(), 10)

    def test_limpiar_y_reinsertar(self):
        a = construir(EJEMPLO)
        a.limpiar()
        self.assertTrue(a.esta_vacio())
        for v in (3, 1, 2):
            a.insertar(v)
        self.assertEqual(a.recorrido_inorden(), [1, 2, 3])
        self.assertEqual(a.obtener_raiz().dato, 3)

    def test_arbol_degenerado_grande_sin_recursion(self):
        a = construir(range(5000))                   # lista enlazada
        self.assertEqual(a.altura(), 5000)
        self.assertEqual(a.contar_hojas(), 1)
        self.assertEqual(a.recorrido_postorden()[-1], 0)
        self.assertEqual(len(a.recorrido_por_niveles()), 5000)

    def test_aleatorio_contra_referencia(self):
        rnd = random.Random(2024)
        a, ref = Arbol(), set()
        for i in range(3000):
            v = rnd.randint(0, 300)
            if rnd.random() < 0.6:
                self.assertEqual(a.insertar(v), v not in ref)
                ref.add(v)
            else:
                self.assertEqual(a.eliminar(v), v in ref)
                ref.discard(v)
            if i % 100 == 0:
                self.assertTrue(es_abb_valido(a))
        self.assertEqual(a.recorrido_inorden(), sorted(ref))
        self.assertEqual(a.contar_nodos(), len(ref))
        self.assertEqual(sorted(a.recorrido_preorden()), sorted(ref))
        self.assertEqual(sorted(a.recorrido_postorden()), sorted(ref))
        self.assertEqual(sorted(a.recorrido_por_niveles()), sorted(ref))


if __name__ == "__main__":
    unittest.main(verbosity=2)
