"""Prueba automática de la interfaz (necesita un servidor X; en Linux sin pantalla:
   xvfb-run -a -s "-screen 0 1500x900x24" python pruebas/prueba_interfaz.py
Ejecuta operaciones reales sobre la ventana, valida resultados y guarda capturas en evidencias/."""
import os, subprocess, sys, time
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)
from tkinter import messagebox

dialogos = []
for nombre in ("showinfo", "showwarning", "showerror"):
    setattr(messagebox, nombre, (lambda n: lambda t, m, **k: dialogos.append((n, t, m)))(nombre))
messagebox.askyesno = lambda t, m, **k: (dialogos.append(("askyesno", t, m)) or True)

from interfaz import AplicacionArbol
OUT = os.path.join(RAIZ, "evidencias")
app = AplicacionArbol()
app.var_velocidad.set(5)

def vivir(ms=150):
    fin = time.time() + ms / 1000
    while time.time() < fin:
        app.update(); time.sleep(0.01)

def esperar():
    while app._ocupado:
        app.update(); time.sleep(0.01)
    vivir(60)

def foto(nombre):
    app.update(); vivir(120)
    subprocess.run(["import", "-window", "root", f"{OUT}/{nombre}.png"], check=True)

def ok(cond, msg):
    print(("OK   " if cond else "FALLA"), msg)
    if not cond: ok.fallos += 1
ok.fallos = 0

def escribir(v):
    app.var_valor.set(v)

vivir(300)
foto("01_arbol_vacio")

# 1-2 validaciones
escribir(""); app.accion_insertar()
ok(dialogos[-1][1] == "Campo vacío", "campo vacío -> aviso")
escribir("abc"); app.accion_insertar()
ok(dialogos[-1][1] == "Dato no válido", "dato no numérico -> aviso")
escribir("3.5"); app.accion_insertar()
ok(dialogos[-1][1] == "Dato no válido", "decimal -> aviso")
escribir("99999"); app.accion_insertar()
ok(dialogos[-1][1] == "Valor fuera de rango", "fuera de rango -> aviso")
escribir("5"); app.accion_buscar()
ok(dialogos[-1][1] == "Árbol vacío", "buscar en árbol vacío -> aviso")
escribir("5"); app.accion_eliminar()
ok(dialogos[-1][1] == "Árbol vacío", "eliminar en árbol vacío -> aviso")
app.accion_recorrido("inorden")
ok(dialogos[-1][1] == "Árbol vacío", "recorrer árbol vacío -> aviso")

# árbol con un único nodo
escribir("50"); app.accion_insertar(); esperar()
ok(app.arbol.contar_nodos() == 1 and app.var_stats["altura"].get() == "1", "un único nodo")
ok("único nodo" in app.var_estado_arbol.get(), "estado: único nodo")
foto("02_un_nodo")

# inserciones
for v in (30, 70, 20, 40, 60, 80, 35, 45, 65):
    escribir(str(v)); app.accion_insertar(); esperar()
ok(app.arbol.recorrido_inorden() == [20,30,35,40,45,50,60,65,70,80], "ABB ordenado tras insertar")
ok(app.var_stats["nodos"].get() == "10" and app.var_stats["altura"].get() == "4"
   and app.var_stats["hojas"].get() == "5", "estadísticas 10/4/5")
ok(app.var_stats["minimo"].get() == "20" and app.var_stats["maximo"].get() == "80", "mín/máx")

# duplicado
n = len(dialogos); escribir("40"); app.accion_insertar(); esperar()
ok(dialogos[-1][1] == "Valor duplicado" and app.arbol.contar_nodos() == 10, "duplicado rechazado")

# búsqueda existente (captura a mitad de animación y al final)
app.var_velocidad.set(2)
escribir("45"); app.accion_buscar()
t0 = time.time()
while len(app.vis._resaltados) < 3 and time.time() - t0 < 5:
    app.update(); time.sleep(0.01)
foto("03_busqueda_en_curso")
esperar()
foto("04_busqueda_encontrada")
ok("encontrado" in app.var_mensaje.get(), "búsqueda existente")
app.var_velocidad.set(5)
vivir(3000)
ok(not app.vis._resaltados, "resaltado temporal se limpia solo")

# búsqueda inexistente
escribir("66"); app.accion_buscar(); esperar()
ok(dialogos[-1][1] == "No encontrado", "búsqueda inexistente -> aviso")
escribir("1234"); app.accion_eliminar(); esperar()
ok(dialogos[-1][1] == "No encontrado" and app.arbol.contar_nodos() == 10, "eliminar inexistente -> aviso")

# recorridos
for k, esperado in (("preorden", [50,30,20,40,35,45,70,60,65,80]),
                    ("inorden", [20,30,35,40,45,50,60,65,70,80]),
                    ("postorden", [20,35,45,40,30,65,60,80,70,50]),
                    ("niveles", [50,30,70,20,40,60,80,35,45,65])):
    app.accion_recorrido(k)
    ok(app.var_recorrido[k].get() == " → ".join(map(str, esperado)), f"recorrido {k}")
foto("05_recorridos")

# recorrido paso a paso
app.var_velocidad.set(3); app.combo.current(1)
app.accion_animar_recorrido()
t0 = time.time()
while len(app.vis._etiquetas) < 6 and time.time() - t0 < 8:
    app.update(); time.sleep(0.01)
foto("06_recorrido_paso_a_paso")
app.var_velocidad.set(5); esperar()
ok(app.var_recorrido["inorden"].get().endswith("80"), "paso a paso completo")
foto("07_recorrido_completo")

# eliminaciones
app.var_velocidad.set(2)
escribir("80"); app.accion_eliminar()
t0 = time.time()
while "eliminar" not in app.vis._resaltados.values() and time.time() - t0 < 8:
    app.update(); time.sleep(0.01)
foto("08_eliminando_hoja")
app.var_velocidad.set(5); esperar()
ok(app.arbol.buscar(80) is None and app.arbol.contar_nodos() == 9, "eliminar hoja")

escribir("60"); app.accion_eliminar(); esperar()
ok(app.arbol.buscar(60) is None and app.arbol.buscar(70).izquierdo.dato == 65, "eliminar nodo con un hijo")

app.var_velocidad.set(2)
escribir("30"); app.accion_eliminar()
t0 = time.time()
while "sucesor" not in app.vis._resaltados.values() and time.time() - t0 < 8:
    app.update(); time.sleep(0.01)
foto("09_eliminando_dos_hijos")
app.var_velocidad.set(5); esperar()
ok(app.arbol.buscar(30) is None and app.arbol.buscar(50).izquierdo.dato == 35, "eliminar nodo con dos hijos")
ok(app.arbol.recorrido_inorden() == [20,35,40,45,50,65,70], "inorden tras eliminaciones")
foto("10_tras_eliminaciones")

# eliminar raíz
escribir("50"); app.accion_eliminar(); esperar()
ok(app.arbol.obtener_raiz().dato == 65, "eliminar raíz")

# limpiar y reinsertar
app.accion_limpiar()
ok(app.arbol.esta_vacio() and app.var_stats["nodos"].get() == "0", "limpiar árbol")
for v in (8, 3, 10):
    escribir(str(v)); app.accion_insertar(); esperar()
ok(app.arbol.recorrido_preorden() == [8, 3, 10], "reinsertar tras limpiar")

# ejemplo y aleatorio
app.accion_ejemplo()
ok(app.arbol.recorrido_inorden() == sorted([50,30,70,20,40,60,80,35,45,65]), "árbol de ejemplo")
foto("11_arbol_ejemplo")
import random; random.seed(7)
app.accion_aleatorio()
ok(8 <= app.arbol.contar_nodos() <= 15, "árbol aleatorio")
foto("12_arbol_aleatorio")

# árbol grande y degenerado: scroll en vez de encimar
app.arbol.limpiar()
for v in range(1, 40):
    app.arbol.insertar(v)
app._refrescar(); vivir(300)
foto("13_arbol_grande_degenerado")
sr = app.canvas.cget("scrollregion")
ok(float(sr.split()[2]) > app.canvas.winfo_width(), f"árbol grande usa scroll (region={sr})")

# clic en nodo copia valor
app.arbol.limpiar(); app._refrescar()
for v in (50, 30, 70): app.arbol.insertar(v)
app._refrescar(); vivir(200)
nodo = app.arbol.buscar(30)
app._al_clic_nodo(nodo)
ok(app.var_valor.get() == "30", "clic en nodo copia el valor")

# redimensionar
app.geometry("1100x700+0+0"); vivir(500); foto("14_ventana_minima")
app.geometry("1500x880+0+0"); vivir(400)
app.arbol.limpiar()
for v in (50,30,70,20,40,60,80,35,45,65): app.arbol.insertar(v)
app._refrescar(); vivir(300); foto("15_ventana_grande")

print("\nDIÁLOGOS MOSTRADOS:", len(dialogos))
print("FALLOS:", ok.fallos)
app.destroy()
sys.exit(1 if ok.fallos else 0)
