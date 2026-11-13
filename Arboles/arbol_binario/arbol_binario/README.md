# 🌳 Árbol Binario de Búsqueda — Python + Tkinter

Aplicación de escritorio para la actividad de **Estructuras de Datos (Unidad: Árboles)**: implementa las clases **`Nodo`** y **`Arbol`** (árbol binario de búsqueda, ABB) y una interfaz gráfica en **Tkinter** que permite insertar, buscar, eliminar, recorrer y visualizar el árbol.

- Python 3.11+ · sin dependencias externas (solo biblioteca estándar).
- Interfaz 100 % Tkinter (`Canvas` para dibujar el árbol).
- Programación orientada a objetos, código modular y documentado.

---

## 1. Estructura del proyecto

```
arbol_binario/
├── main.py            # Punto de entrada
├── nodo.py            # Clase Nodo
├── arbol.py           # Clase Arbol (ABB) y todos sus algoritmos
├── visualizador.py    # Dibujo y distribución de nodos en el Canvas
├── interfaz.py        # Ventana, botones, campos y eventos
├── requirements.txt   # (sin dependencias externas)
├── README.md
├── pruebas/
│   ├── test_arbol.py          # 19 pruebas unitarias de Nodo y Arbol
│   └── prueba_interfaz.py     # Prueba automática de la GUI + capturas
└── evidencias/        # Capturas de la aplicación funcionando
```

## 2. Ejecución

```bash
cd arbol_binario
python main.py          # en Windows también: py main.py
```

> **Linux:** si aparece `No module named 'tkinter'`, instala `sudo apt install python3-tk`.
> **Windows / macOS:** tkinter ya viene con el instalador oficial de Python.

Pruebas:

```bash
python -m unittest discover -s pruebas -v          # lógica de Nodo y Arbol
```

## 3. Cómo se usa

| Zona | Contenido |
|------|-----------|
| **Panel izquierdo** | Campo de valor · **Insertar** (o Enter) · **Buscar** · **Eliminar** · Árbol de ejemplo · Aleatorizar · Limpiar |
| **Centro** | Canvas con el árbol, resultados de los 4 recorridos y leyenda de colores |
| **Panel derecho** | Nodos, altura, hojas, raíz, mínimo, máximo · estado del árbol · botones de recorridos · recorrido **paso a paso** con control de velocidad |

Colores: 🟣 raíz · 🔵 nodo interno · 🟢 hoja · 🟠 nodo visitado · 🟡 encontrado / nuevo · 🔴 error o nodo que se elimina · 🟧 sucesor inorden.
Al hacer **clic en un nodo** su valor se copia al campo de texto.

## 4. Decisiones de diseño

- **Duplicados:** no se permiten. `insertar` devuelve `False` y el árbol no cambia; la interfaz avisa con un cuadro de diálogo.
- **Altura:** se usa la definición de la presentación de clase: es el **número máximo de niveles** (raíz = nivel 1; árbol vacío = 0).
- **Algoritmos iterativos:** evitan `RecursionError` aun con árboles degenerados (probado con 5000 nodos ordenados).
- **Sin encimar nodos:** cada nodo ocupa su propia columna (posición inorden); si el árbol no cabe en la ventana aparecen barras de desplazamiento.
- **Estabilidad:** durante una animación los botones se bloquean; cualquier error inesperado desbloquea la interfaz.

---

## 5. Clase `Nodo` (`nodo.py`)

Representa cada elemento del árbol.

| Atributo | Descripción |
|----------|-------------|
| `dato` | Valor almacenado |
| `izquierdo` | Hijo izquierdo (valores menores) |
| `derecho` | Hijo derecho (valores mayores) |
| `padre` | Nodo padre (`None` en la raíz) |

| Método | Qué hace |
|--------|----------|
| `__init__(dato, padre=None)` | Inicializa un nodo sin hijos |
| `asignar_izquierdo(nodo)` / `asignar_derecho(nodo)` | Asignan el hijo y actualizan su `padre` |
| `es_hoja()` | `True` si no tiene hijos |
| `tiene_hijos()` | `True` si tiene al menos un hijo |
| `numero_hijos()` | Grado del nodo (0, 1 o 2) |
| `es_raiz()` | `True` si no tiene padre |
| `hijos()` | Lista de hijos existentes |
| `tipo()` | `'raíz'`, `'interno'` u `'hoja'` |
| `obtener_info()` | Diccionario con dato, tipo, grado, padre, izquierdo, derecho |

## 6. Clase `Arbol` (`arbol.py`)

Árbol binario de búsqueda: menores a la izquierda, mayores a la derecha.

| # | Método | Descripción | Complejidad* |
|---|--------|-------------|--------------|
| 1 | `insertar(dato)` | Baja comparando desde la raíz y coloca el nodo como hoja. Devuelve `False` si el dato ya existe | O(h) |
| 2 | `buscar(dato)` | Devuelve el `Nodo` o `None` | O(h) |
| 3 | `eliminar(dato)` | Tres casos: **hoja** (se desconecta), **un hijo** (el hijo ocupa su lugar), **dos hijos** (toma el valor de su sucesor inorden y se elimina el sucesor) | O(h) |
| 4 | `obtener_raiz()` | Devuelve el nodo raíz | O(1) |
| 5 | `esta_vacio()` | `True` si no hay raíz | O(1) |
| 6 | `altura()` | Niveles máximos, recorriendo por niveles | O(n) |
| 7 | `contar_nodos()` | Total de nodos | O(n) |
| 8 | `contar_hojas()` | Nodos sin hijos | O(n) |
| 9 | `recorrido_preorden()` | Raíz → Izq → Der | O(n) |
| 10 | `recorrido_inorden()` | Izq → Raíz → Der (devuelve los datos ordenados) | O(n) |
| 11 | `recorrido_postorden()` | Izq → Der → Raíz | O(n) |
| 12 | `recorrido_por_niveles()` | Amplitud con una cola (`deque`) | O(n) |
| 13 | `limpiar()` | Vacía el árbol | O(1) |
| 14 | `encontrar_minimo()` | Baja siempre por la izquierda | O(h) |
| 15 | `encontrar_maximo()` | Baja siempre por la derecha | O(h) |

\* *h = altura del árbol, n = número de nodos.*

Métodos de apoyo para la interfaz: `camino_busqueda(dato)` (nodos visitados, para animar), `caso_eliminacion(dato)` (`'hoja'`, `'un_hijo'`, `'dos_hijos'`), `sucesor_inorden(dato)`. Los cuatro recorridos aceptan `nodos=True` para devolver objetos `Nodo` (recorrido paso a paso). La clase también soporta `len(arbol)`, `dato in arbol` e iteración inorden.

## 7. Verificación realizada

Lista pedida en la actividad, comprobada con `pruebas/test_arbol.py` y `pruebas/prueba_interfaz.py`:

1. Insertar varios valores ✔ · 2. El ABB mantiene el orden ✔ · 3. Buscar existente ✔ · 4. Buscar inexistente ✔
5. Eliminar hoja ✔ · 6. Eliminar nodo con un hijo ✔ · 7. Eliminar nodo con dos hijos ✔ (y la raíz)
8. Los cuatro recorridos ✔ · 9. Altura y cantidad de nodos ✔ · 10. Limpiar y reinsertar ✔

Con el árbol de ejemplo (inserción: 50, 30, 70, 20, 40, 60, 80, 35, 45, 65):

| Recorrido | Resultado |
|-----------|-----------|
| Preorden | 50 30 20 40 35 45 70 60 65 80 |
| Inorden | 20 30 35 40 45 50 60 65 70 80 |
| Postorden | 20 35 45 40 30 65 60 80 70 50 |
| Por niveles | 50 30 70 20 40 60 80 35 45 65 |

Nodos 10 · altura 4 · hojas 5 · mínimo 20 · máximo 80.

Las capturas están en la carpeta [`evidencias/`](evidencias/).

## 8. Subir el proyecto a GitHub

```bash
cd arbol_binario
git init
git add .
git commit -m "Árbol binario de búsqueda con Tkinter (clases Nodo y Arbol)"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/arbol-binario-tkinter.git
git push -u origin main
```

(Crea antes el repositorio vacío en github.com → *New repository*.)
