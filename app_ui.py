"""
Interfaz gráfica moderna (PyQt6) para el TP3 - Gestión de Shopping.
Consume directamente las funciones, clases y archivos de datos del archivo original
`TP3-Gugliermino-Zariaga-Garcia-Lopez .py` sin modificarlo.
"""

from __future__ import annotations

import builtins
import contextlib
import datetime
import importlib.util
import io
import os
import pickle
import sys
import warnings
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# ---------------------------------------------------------------------------
# Carga segura del módulo TP3 original sin modificarlo
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
TP3_FILE = BASE_DIR / "TP3-Gugliermino-Zariaga-Garcia-Lopez .py"


def load_tp3_module():
    """
    Importa `TP3-Gugliermino-Zariaga-Garcia-Lopez .py` sin modificarlo.
    - Ejecuta el archivo con __name__ == '__main__' temporalmente para que pickle
      mantenga exactamente el mismo nombre de módulo y tamaño de registro en bytes
      (274 bytes para Local, 408 bytes para Promocion, etc.).
    - Intercepta `input()` durante la carga para que `ini()` salga con opción '3'.
    - Reabre los archivos binarios usando `tp3.abrir(...)` ya que el script los
      cierra al finalizar `ini()`.
    """
    os.chdir(BASE_DIR)
    warnings.filterwarnings("ignore", category=SyntaxWarning)

    if not TP3_FILE.exists():
        raise FileNotFoundError(f"No se encontró el archivo original: {TP3_FILE}")

    spec = importlib.util.spec_from_file_location("__main__", str(TP3_FILE))
    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo crear el spec de importación para el TP3.")

    tp3 = importlib.util.module_from_spec(spec)
    orig_main = sys.modules["__main__"]
    orig_input = builtins.input
    orig_system = os.system

    try:
        sys.modules["__main__"] = tp3
        builtins.input = lambda *args, **kwargs: "3"
        os.system = lambda *args, **kwargs: 0
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(tp3)
    finally:
        sys.modules["__main__"] = orig_main
        builtins.input = orig_input
        os.system = orig_system

    # Exponer las clases en el __main__ real para que pickle.load/dump
    # resuelva __main__.Usuario, __main__.Local, etc. de forma 100% compatible.
    for cls_name in ("Usuario", "Local", "Promocion", "UsoPromocion"):
        setattr(orig_main, cls_name, getattr(tp3, cls_name))

    # Reabrir los archivos binarios usando la función `abrir` del TP3
    tp3.f_usuarios = tp3.abrir(tp3.ruta_usuarios)
    tp3.f_locales = tp3.abrir(tp3.ruta_locales)
    tp3.f_promociones = tp3.abrir(tp3.ruta_promociones)
    tp3.f_usoPromociones = tp3.abrir(tp3.ruta_usoPromociones)

    # Sincronizar tamaños actuales
    tp3.tamaño_usuarios = os.path.getsize(tp3.ruta_usuarios)
    tp3.tamaño_locales = os.path.getsize(tp3.ruta_locales)

    return tp3


# ---------------------------------------------------------------------------
# Adaptador de servicios que consume únicamente las funciones y datos de TP3
# ---------------------------------------------------------------------------


class TP3Service:
    """Capa delgada sobre el módulo TP3 original para consumo desde Qt6."""

    def __init__(self, tp3_mod: Any) -> None:
        self.tp3 = tp3_mod
        self.current_user: dict[str, str] | None = None

    def close(self) -> None:
        for attr in ("f_locales", "f_usuarios", "f_promociones", "f_usoPromociones"):
            fh = getattr(self.tp3, attr, None)
            if fh and not fh.closed:
                fh.close()

    def _sync_sizes(self) -> None:
        self.tp3.tamaño_usuarios = os.path.getsize(self.tp3.ruta_usuarios)
        self.tp3.tamaño_locales = os.path.getsize(self.tp3.ruta_locales)

    # -- Lectura de registros desde los file handles de TP3 -----------------

    def get_all_usuarios(self) -> list[Any]:
        f = self.tp3.f_usuarios
        sz = os.path.getsize(self.tp3.ruta_usuarios)
        rows = []
        f.seek(0)
        while f.tell() < sz:
            rows.append(pickle.load(f))
        f.seek(0)
        return rows

    def get_all_locales(self) -> list[Any]:
        f = self.tp3.f_locales
        sz = os.path.getsize(self.tp3.ruta_locales)
        rows = []
        f.seek(0)
        while f.tell() < sz:
            rows.append(pickle.load(f))
        f.seek(0)
        return rows

    def get_all_promociones(self) -> list[Any]:
        f = self.tp3.f_promociones
        sz = os.path.getsize(self.tp3.ruta_promociones)
        rows = []
        f.seek(0)
        while f.tell() < sz:
            rows.append(pickle.load(f))
        f.seek(0)
        return rows

    def get_all_usos(self) -> list[Any]:
        f = self.tp3.f_usoPromociones
        sz = os.path.getsize(self.tp3.ruta_usoPromociones)
        rows = []
        f.seek(0)
        while f.tell() < sz:
            rows.append(pickle.load(f))
        f.seek(0)
        return rows

    def get_local_map_by_code(self) -> dict[int, Any]:
        return {int(loc.codigo): loc for loc in self.get_all_locales()}

    def get_user_map_by_code(self) -> dict[int, Any]:
        return {int(u.codigo): u for u in self.get_all_usuarios()}

    # -- Autenticación y usuarios -------------------------------------------

    def authenticate(self, correo: str, clave: str) -> tuple[bool, str]:
        correo = correo.strip()
        if not correo or not clave:
            return False, "Ingrese correo y contraseña."

        self.tp3.f_usuarios.seek(0)
        existe = self.tp3.verifNombre_n(correo, "correo")
        if not existe:
            return False, "Usuario inexistente."

        if clave != self.tp3.val_clave:
            return False, "Contraseña incorrecta."

        self.tp3.correo = correo
        cod = self.tp3.busqUsuarioActual()
        tipo = self.tp3.tipo_usuario.rstrip(" ")
        self.current_user = {
            "codigo": self.tp3.convertir_n(cod),
            "codigo_int": str(cod),
            "correo": correo,
            "tipo": tipo,
        }
        return True, "Ingreso exitoso."

    def logout(self) -> None:
        self.current_user = None
        self.tp3.correo = ""

    def register_user(self, correo: str, clave: str, tipo_code: str) -> tuple[bool, str]:
        """Registra cliente ('cli') o dueño ('dueño') usando la lógica del TP3."""
        correo = correo.strip()
        if not correo or "@" not in correo:
            return False, "Ingrese un correo electrónico válido."
        if len(correo) > 100:
            return False, "El correo no puede superar los 100 caracteres."
        if not clave:
            return False, "La contraseña no puede estar vacía."
        if len(clave) > 8:
            return False, "La contraseña debe tener como máximo 8 caracteres (límite del TP3)."

        self.tp3.f_usuarios.seek(0)
        if self.tp3.verifNombre_n(correo, "correo"):
            return False, "Ya existe un usuario registrado con ese correo."

        nuevo = self.tp3.Usuario()
        nuevo.correo = correo.ljust(100)
        nuevo.clave = clave.ljust(8)
        nuevo.tipo = ("cliente" if tipo_code == "cli" else "Dueno de local").ljust(20)

        self.tp3.cod_usuario += 1
        nuevo.codigo = self.tp3.convertir_n(self.tp3.cod_usuario)

        self.tp3.ultima_fila()
        pickle.dump(nuevo, self.tp3.f_usuarios)
        self.tp3.f_usuarios.flush()
        os.fsync(self.tp3.f_usuarios.fileno())
        self._sync_sizes()
        return True, f"Usuario registrado con éxito (Código {nuevo.codigo})."

    # -- Locales ------------------------------------------------------------

    def get_rubro_stats(self) -> list[tuple[str, int]]:
        """Usa `tp3.ar_orden` para ordenar los rubros de mayor a menor."""
        ar_cont = [
            self.tp3.cont_indumentaria,
            self.tp3.cont_comida,
            self.tp3.cont_perfumeria,
        ]
        ar_rub = self.tp3.ar_rubro[:]
        self.tp3.ar_orden(ar_cont, 3, ar_rub)
        return [(ar_rub[2], ar_cont[2]), (ar_rub[1], ar_cont[1]), (ar_rub[0], ar_cont[0])]

    def get_available_slots(self) -> int:
        sz = os.path.getsize(self.tp3.ruta_locales)
        usados = int(sz / 274)
        return max(0, 50 - usados)

    def create_local(self, nombre: str, ubicacion: str, rubro: str, cod_usuario_str: str) -> tuple[bool, str]:
        nombre = nombre.strip()
        ubicacion = ubicacion.strip()
        rubro = rubro.strip().lower()

        if self.get_available_slots() <= 0:
            return False, "No hay espacio disponible (límite máximo de 50 locales)."
        if not nombre or nombre == "*":
            return False, "Ingrese un nombre de local válido."
        if len(nombre) > 50:
            return False, "El nombre no puede superar los 50 caracteres."
        if not ubicacion:
            return False, "Ingrese la ubicación del local."
        if len(ubicacion) > 50:
            return False, "La ubicación no puede superar los 50 caracteres."
        if rubro not in self.tp3.ar_rubro:
            return False, f"Rubro inválido. Opciones: {', '.join(self.tp3.ar_rubro)}."

        # Verificar duplicado con la búsqueda dicotómica del TP3
        if os.path.getsize(self.tp3.ruta_locales) > 0 and self.tp3.dico(nombre):
            return False, "Ya existe un local con ese nombre."

        # Validar dueño de local usando verifNombre_n del TP3
        try:
            cod_u = self.tp3.convertir_n(int(cod_usuario_str))
        except ValueError:
            return False, "El código de usuario debe ser numérico."

        self.tp3.f_usuarios.seek(0)
        if not self.tp3.verifNombre_n(cod_u, "codigo"):
            return False, "El código de usuario no existe."
        if self.tp3.fila_usuarios.tipo.rstrip(" ") != "Dueno de local":
            return False, "El código seleccionado no corresponde a un Dueño de local."

        nuevo = self.tp3.Local()
        nuevo.nombre = nombre.ljust(50)
        nuevo.ubicacion = ubicacion.ljust(50)
        nuevo.rubro = rubro.ljust(50)
        nuevo.codUsuario = cod_u
        self.tp3.cod_local += 1
        nuevo.codigo = self.tp3.convertir_n(self.tp3.cod_local)
        nuevo.estado = "A"

        self.tp3.operar_contadores(rubro, "aumentar")
        self.tp3.cantidadLoc += 1
        self.tp3.guardado_locales(nuevo)
        self.tp3.orden_bi()
        self._sync_sizes()
        return True, f"Local '{nombre}' creado con código {nuevo.codigo}."

    def update_local(
        self,
        codigo_str: str,
        nombre: str,
        ubicacion: str,
        rubro: str,
        cod_usuario_str: str,
    ) -> tuple[bool, str]:
        self._sync_sizes()
        if self.tp3.val_datos_local(codigo_str):
            return False, "No se encontró el local seleccionado."

        fila = self.tp3.fila_local
        pos = self.tp3.pos

        nombre = nombre.strip()
        ubicacion = ubicacion.strip()
        rubro = rubro.strip().lower()

        if not nombre or nombre == "*":
            return False, "Nombre inválido."
        if len(nombre) > 50 or len(ubicacion) > 50:
            return False, "Nombre y ubicación deben tener hasta 50 caracteres."
        if not ubicacion:
            return False, "La ubicación no puede estar vacía."
        if rubro not in self.tp3.ar_rubro:
            return False, "Rubro inválido."

        nombre_anterior = fila.nombre.rstrip(" ")
        if nombre != nombre_anterior and self.tp3.dico(nombre):
            return False, "Ya existe otro local con ese nombre."

        try:
            cod_u = self.tp3.convertir_n(int(cod_usuario_str))
        except ValueError:
            return False, "Código de usuario inválido."

        self.tp3.f_usuarios.seek(0)
        if not self.tp3.verifNombre_n(cod_u, "codigo"):
            return False, "El código de usuario no existe."
        if self.tp3.fila_usuarios.tipo.rstrip(" ") != "Dueno de local":
            return False, "El usuario seleccionado no es Dueño de local."

        rubro_anterior = fila.rubro.rstrip(" ")
        if fila.estado == "A" and rubro != rubro_anterior:
            self.tp3.operar_contadores(rubro_anterior, "restar")
            self.tp3.operar_contadores(rubro, "aumentar")

        fila.nombre = nombre.ljust(50)
        fila.ubicacion = ubicacion.ljust(50)
        fila.rubro = rubro.ljust(50)
        fila.codUsuario = cod_u

        self.tp3.actualizar_fila(pos, fila)
        if nombre != nombre_anterior:
            self.tp3.orden_bi()
        self._sync_sizes()
        return True, f"Local {codigo_str} actualizado correctamente."

    def toggle_local_estado(self, codigo_str: str) -> tuple[bool, str]:
        self._sync_sizes()
        if self.tp3.val_datos_local(codigo_str):
            return False, "No se encontró el local."

        fila = self.tp3.fila_local
        pos = self.tp3.pos
        rubro = fila.rubro.rstrip(" ")

        if fila.estado == "A":
            fila.estado = "B"
            self.tp3.operar_contadores(rubro, "restar")
            msg = f"Local {codigo_str} dado de baja."
        else:
            fila.estado = "A"
            self.tp3.operar_contadores(rubro, "aumentar")
            msg = f"Local {codigo_str} reactivado."

        self.tp3.actualizar_fila(pos, fila)
        self._sync_sizes()
        return True, msg

    def get_mapa_locales(self) -> list[tuple[int, str]]:
        """Usa `tp3.carga_locales()` y retorna las 50 celdas (codigo, estado)."""
        for i in range(50):
            self.tp3.ar_locales_cod[i][1] = 0
            self.tp3.ar_locales_estado[i] = ""
        self.tp3.carga_locales()
        return [
            (self.tp3.ar_locales_cod[i][1], self.tp3.ar_locales_estado[i])
            for i in range(50)
        ]

    # -- Promociones --------------------------------------------------------

    def update_promocion_estado(self, cod_promo_int: int, aprobar: bool) -> tuple[bool, str]:
        tamaño_prom = os.path.getsize(self.tp3.ruta_promociones)
        if tamaño_prom == 0:
            return False, "No existen promociones cargadas."

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            invalida = self.tp3.valid_cod_promocion(cod_promo_int, tamaño_prom)

        if invalida:
            err = buf.getvalue().strip() or "La promoción no existe o ya fue actualizada."
            return False, err

        pos = self.tp3.posicion
        self.tp3.f_promociones.seek(pos - 408)
        fila_prom = pickle.load(self.tp3.f_promociones)
        fila_prom.estado = ("Aprobada" if aprobar else "Rechazada").ljust(10)

        self.tp3.f_promociones.seek(pos - 408)
        pickle.dump(fila_prom, self.tp3.f_promociones)
        self.tp3.f_promociones.flush()
        self.tp3.f_promociones.seek(0)
        accion = "aprobada" if aprobar else "rechazada"
        return True, f"Promoción #{self.tp3.convertir_n(cod_promo_int)} {accion} correctamente."

    def create_promocion(
        self,
        cod_local_int: int,
        texto: str,
        fecha_desde: datetime.date,
        fecha_hasta: datetime.date,
        dias_semana: list[int],
    ) -> tuple[bool, str]:
        texto = texto.strip()
        if not texto:
            return False, "Ingrese una descripción para la promoción."
        if len(texto) > 200:
            return False, "La descripción no puede superar los 200 caracteres."
        if self.tp3.val_cod_local(cod_local_int):
            return False, "El código de local seleccionado no existe."
        if fecha_desde < self.tp3.fecha_actual:
            return False, "La fecha de inicio no puede ser anterior a hoy."
        if fecha_desde > fecha_hasta:
            return False, "La fecha de inicio debe ser menor o igual a la fecha de fin."
        if not any(dias_semana):
            return False, "Seleccione al menos un día de la semana."

        cod_prom = self.tp3.CantProm()
        fila_prom = self.tp3.Promocion()
        fila_prom.codPromo = self.tp3.convertir_n(cod_prom)
        fila_prom.textoPromo = texto.ljust(200)
        fila_prom.fechaDesdePromo = fecha_desde.strftime("%d/%m/%Y")
        fila_prom.fechaHastaPromo = fecha_hasta.strftime("%d/%m/%Y")
        fila_prom.diasSemana = list(dias_semana)
        fila_prom.estado = "Pendiente".ljust(10)
        fila_prom.codLocal = self.tp3.convertir_n(cod_local_int)

        tamaño_prom = os.path.getsize(self.tp3.ruta_promociones)
        self.tp3.f_promociones.seek(tamaño_prom)
        self.tp3.guardado_promociones(fila_prom)
        return True, f"Promoción #{fila_prom.codPromo} creada en estado Pendiente."

    def get_owner_locales(self) -> list[Any]:
        cod_dueño = self.tp3.busqUsuarioActual()
        return [loc for loc in self.get_all_locales() if int(loc.codUsuario) == cod_dueño]

    def get_owner_promociones(self) -> list[Any]:
        cod_dueño = self.tp3.busqUsuarioActual()
        result = []
        for p in self.get_all_promociones():
            try:
                if self.tp3.busqDueñoProm(int(p.codLocal)) == cod_dueño:
                    result.append(p)
            except EOFError:
                pass
        return result

    def search_promociones_cliente(
        self, cod_local_str: str, fecha_busq: datetime.date
    ) -> list[Any]:
        dia = fecha_busq.weekday()
        matches = []
        for p in self.get_all_promociones():
            if p.codLocal != cod_local_str:
                continue
            if p.estado.strip(" ") != "Aprobada":
                continue
            f_des = datetime.datetime.strptime(p.fechaDesdePromo, "%d/%m/%Y").date()
            f_has = datetime.datetime.strptime(p.fechaHastaPromo, "%d/%m/%Y").date()
            if f_des <= fecha_busq <= f_has and p.diasSemana[dia] == 1:
                matches.append(p)
        return matches

    def redeem_promocion(self, cod_promo_int: int) -> tuple[bool, str]:
        if os.path.getsize(self.tp3.ruta_promociones) == 0:
            return False, "No hay promociones registradas."

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            invalida = self.tp3.val_cod_prom(cod_promo_int)

        if invalida:
            raw = buf.getvalue()
            # Limpiar secuencias ANSI de colorama si aparecieran
            clean = "".join(ch for ch in raw if ch.isprintable() or ch == "\n").strip()
            for seq in ("[91m", "[93m", "[39m", "[0m"):
                clean = clean.replace(seq, "")
            return False, clean or "La promoción no es válida para hoy."

        cod_cliente = self.tp3.busqUsuarioActual()
        uso = self.tp3.UsoPromocion()
        uso.codCliente = self.tp3.convertir_n(cod_cliente)
        uso.codPromo = self.tp3.convertir_n(cod_promo_int)
        uso.fechaUsoPromo = self.tp3.fecha_actual.strftime("%d/%m/%Y")

        tamaño_uso = os.path.getsize(self.tp3.ruta_usoPromociones)
        self.tp3.f_usoPromociones.seek(tamaño_uso)
        self.tp3.guardado_usoPromociones(uso)
        return True, f"¡Descuento #{uso.codPromo} aplicado y registrado con éxito!"

    def get_reporte_usos(
        self,
        fecha_desde: datetime.date,
        fecha_hasta: datetime.date,
        solo_dueño: bool = False,
    ) -> list[dict[str, Any]]:
        loc_map = self.get_local_map_by_code()
        owner_local_ids = None
        if solo_dueño:
            owner_local_ids = {int(loc.codigo) for loc in self.get_owner_locales()}

        rows = []
        for p in self.get_all_promociones():
            if p.estado.strip(" ") != "Aprobada":
                continue
            cod_loc = int(p.codLocal)
            if owner_local_ids is not None and cod_loc not in owner_local_ids:
                continue
            f_des = datetime.datetime.strptime(p.fechaDesdePromo, "%d/%m/%Y").date()
            f_has = datetime.datetime.strptime(p.fechaHastaPromo, "%d/%m/%Y").date()
            if f_des >= fecha_desde and f_has <= fecha_hasta:
                cant = self.tp3.CantUsos(int(p.codPromo), fecha_desde, fecha_hasta)
                loc_obj = loc_map.get(cod_loc)
                rows.append(
                    {
                        "codPromo": p.codPromo,
                        "codLocal": p.codLocal,
                        "nombreLocal": loc_obj.nombre.strip(" ") if loc_obj else f"Local {p.codLocal}",
                        "texto": p.textoPromo.strip(" "),
                        "desde": p.fechaDesdePromo,
                        "hasta": p.fechaHastaPromo,
                        "usos": cant,
                    }
                )
        return rows


# ---------------------------------------------------------------------------
# Hoja de estilos moderna (Dark Slate + Indigo/Emerald)
# ---------------------------------------------------------------------------

STYLESHEET = """
QMainWindow, QWidget#RootWidget {
    background-color: #0B1120;
    color: #F8FAFC;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}

QFrame#Sidebar {
    background-color: #0F172A;
    border-right: 1px solid #1E293B;
}

QFrame#TopBar {
    background-color: #0F172A;
    border-bottom: 1px solid #1E293B;
}

QFrame#Card, QFrame#AuthCard, QFrame#HeroCard {
    background-color: #111C33;
    border: 1px solid #1E293B;
    border-radius: 14px;
}

QFrame#HeroCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1E1B4B, stop:0.55 #0F172A, stop:1 #064E3B);
    border: 1px solid #312E81;
}

QFrame#KpiCard {
    background-color: #111C33;
    border: 1px solid #1E293B;
    border-radius: 12px;
}

QLabel#TitleLarge {
    font-size: 24px;
    font-weight: 700;
    color: #F8FAFC;
}

QLabel#TitleMedium {
    font-size: 17px;
    font-weight: 600;
    color: #F8FAFC;
}

QLabel#Subtitle {
    font-size: 13px;
    color: #94A3B8;
}

QLabel#SectionLabel {
    font-size: 11px;
    font-weight: 700;
    color: #64748B;
    letter-spacing: 1px;
}

QLabel#KpiValue {
    font-size: 28px;
    font-weight: 700;
    color: #F8FAFC;
}

QLabel#KpiLabel {
    font-size: 12px;
    color: #94A3B8;
}

QLineEdit, QComboBox, QDateEdit, QTextEdit {
    background-color: #0B1120;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    min-height: 20px;
    selection-background-color: #6366F1;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
    border: 1px solid #6366F1;
}

QComboBox::drop-down, QDateEdit::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #0F172A;
    color: #F8FAFC;
    border: 1px solid #334155;
    selection-background-color: #4F46E5;
}

QPushButton {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #334155;
}

QPushButton:pressed {
    background-color: #1E293B;
}

QPushButton#PrimaryBtn {
    background-color: #6366F1;
    border: 1px solid #818CF8;
    color: #FFFFFF;
}

QPushButton#PrimaryBtn:hover {
    background-color: #4F46E5;
}

QPushButton#SuccessBtn {
    background-color: #059669;
    border: 1px solid #10B981;
    color: #FFFFFF;
}

QPushButton#SuccessBtn:hover {
    background-color: #047857;
}

QPushButton#DangerBtn {
    background-color: #DC2626;
    border: 1px solid #EF4444;
    color: #FFFFFF;
}

QPushButton#DangerBtn:hover {
    background-color: #B91C1C;
}

QPushButton#GhostBtn {
    background-color: transparent;
    border: 1px solid #334155;
    color: #CBD5E1;
}

QPushButton#GhostBtn:hover {
    background-color: #1E293B;
    color: #F8FAFC;
}

QPushButton#NavBtn {
    background-color: transparent;
    border: none;
    border-radius: 9px;
    text-align: left;
    padding: 10px 14px;
    color: #94A3B8;
    font-weight: 500;
    font-size: 13px;
}

QPushButton#NavBtn:hover {
    background-color: #1E293B;
    color: #F8FAFC;
}

QPushButton#NavBtn[active="true"] {
    background-color: #312E81;
    color: #FFFFFF;
    font-weight: 600;
}

QPushButton#DayPill {
    background-color: #0B1120;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 10px;
    color: #94A3B8;
    font-weight: 600;
    min-width: 44px;
}

QPushButton#DayPill:checked {
    background-color: #4F46E5;
    border: 1px solid #818CF8;
    color: #FFFFFF;
}

QTableWidget {
    background-color: #0F172A;
    alternate-background-color: #111C33;
    border: 1px solid #1E293B;
    border-radius: 10px;
    gridline-color: #1E293B;
    color: #E2E8F0;
    selection-background-color: #312E81;
    selection-color: #FFFFFF;
}

QTableWidget::item {
    padding: 6px 10px;
}

QHeaderView::section {
    background-color: #16223A;
    color: #94A3B8;
    font-weight: 600;
    font-size: 12px;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #1E293B;
}

QTabWidget::pane {
    border: none;
    background: transparent;
}

QTabBar::tab {
    background-color: #0F172A;
    color: #94A3B8;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 8px 16px;
    margin-right: 6px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #4F46E5;
    color: #FFFFFF;
    border-color: #6366F1;
}

QScrollBar:vertical {
    background: #0B1120;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 5px;
    min-height: 24px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QMessageBox, QDialog {
    background-color: #0F172A;
    color: #F8FAFC;
}
"""


# ---------------------------------------------------------------------------
# Helpers de UI
# ---------------------------------------------------------------------------

DAYS_SHORT = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def format_dias(dias_list: list[int]) -> str:
    activos = [DAYS_SHORT[i] for i in range(min(7, len(dias_list))) if dias_list[i] == 1]
    return " · ".join(activos) if activos else "Ninguno"


def make_badge(text: str, bg: str, fg: str = "#FFFFFF") -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    lbl.setStyleSheet(
        f"background-color: {bg}; color: {fg}; border-radius: 10px; "
        f"padding: 4px 12px; font-size: 11px; font-weight: 700;"
    )
    return lbl


def make_kpi_card(label: str, value: str, accent: str = "#6366F1") -> tuple[QFrame, QLabel]:
    card = QFrame()
    card.setObjectName("KpiCard")
    card.setStyleSheet(
        f"QFrame#KpiCard {{ background-color: #111C33; border: 1px solid #1E293B; "
        f"border-left: 4px solid {accent}; border-radius: 12px; }}"
    )
    lay = QVBoxLayout(card)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(4)

    lbl_top = QLabel(label)
    lbl_top.setObjectName("KpiLabel")
    lbl_val = QLabel(value)
    lbl_val.setObjectName("KpiValue")

    lay.addWidget(lbl_top)
    lay.addWidget(lbl_val)
    return card, lbl_val


def style_table(table: QTableWidget) -> None:
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    table.verticalHeader().setDefaultSectionSize(38)


def qdate_to_date(qd: QDate) -> datetime.date:
    return datetime.date(qd.year(), qd.month(), qd.day())


def date_to_qdate(d: datetime.date) -> QDate:
    return QDate(d.year, d.month, d.day)


# ---------------------------------------------------------------------------
# Diálogo para crear / editar Local
# ---------------------------------------------------------------------------


class LocalDialog(QDialog):
    def __init__(
        self,
        service: TP3Service,
        parent: QWidget | None = None,
        local_obj: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self.service = service
        self.local_obj = local_obj
        self.setWindowTitle("Modificar Local" if local_obj else "Nuevo Local")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(22, 22, 22, 22)

        title = QLabel("Modificar Local" if local_obj else "Crear Nuevo Local")
        title.setObjectName("TitleMedium")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.in_nombre = QLineEdit()
        self.in_nombre.setMaxLength(50)
        self.in_nombre.setPlaceholderText("Ej: Zara, Havanna, Juleriaque...")

        self.in_ubicacion = QLineEdit()
        self.in_ubicacion.setMaxLength(50)
        self.in_ubicacion.setPlaceholderText("Ej: Planta Baja - Ala Norte")

        self.in_rubro = QComboBox()
        self.in_rubro.addItems(["indumentaria", "comida", "perfumeria"])

        self.in_dueno = QComboBox()
        duenos = [
            u for u in self.service.get_all_usuarios() if u.tipo.rstrip(" ") == "Dueno de local"
        ]
        for d in duenos:
            self.in_dueno.addItem(f"[{d.codigo}] {d.correo.strip(' ')}", d.codigo)

        if local_obj is not None:
            self.in_nombre.setText(local_obj.nombre.rstrip(" "))
            self.in_ubicacion.setText(local_obj.ubicacion.rstrip(" "))
            idx_r = self.in_rubro.findText(local_obj.rubro.rstrip(" "))
            if idx_r >= 0:
                self.in_rubro.setCurrentIndex(idx_r)
            idx_u = self.in_dueno.findData(local_obj.codUsuario)
            if idx_u >= 0:
                self.in_dueno.setCurrentIndex(idx_u)

        form.addRow("Nombre:", self.in_nombre)
        form.addRow("Ubicación:", self.in_ubicacion)
        form.addRow("Rubro:", self.in_rubro)
        form.addRow("Dueño de local:", self.in_dueno)
        layout.addLayout(form)

        if not duenos:
            warn = QLabel("⚠ No hay cuentas de 'Dueño de local' creadas. Cree una primero.")
            warn.setStyleSheet("color: #F59E0B; font-size: 12px;")
            layout.addWidget(warn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("PrimaryBtn")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        if self.in_dueno.count() == 0:
            QMessageBox.warning(self, "Atención", "Debe existir al menos un Dueño de local.")
            return

        nombre = self.in_nombre.text()
        ubicacion = self.in_ubicacion.text()
        rubro = self.in_rubro.currentText()
        cod_dueno = self.in_dueno.currentData()

        if self.local_obj is None:
            ok, msg = self.service.create_local(nombre, ubicacion, rubro, cod_dueno)
        else:
            ok, msg = self.service.update_local(
                self.local_obj.codigo, nombre, ubicacion, rubro, cod_dueno
            )

        if ok:
            QMessageBox.information(self, "Operación exitosa", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Validación", msg)


# ---------------------------------------------------------------------------
# Pantalla de Login y Registro
# ---------------------------------------------------------------------------


class AuthScreen(QWidget):
    login_success = pyqtSignal()

    def __init__(self, service: TP3Service) -> None:
        super().__init__()
        self.service = service
        self.intentos_restantes = 3
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.setSpacing(32)

        # Panel izquierdo: Hero / Presentación
        hero = QFrame()
        hero.setObjectName("HeroCard")
        hero.setMinimumWidth(420)
        hero_lay = QVBoxLayout(hero)
        hero_lay.setContentsMargins(36, 36, 36, 36)
        hero_lay.setSpacing(16)

        pill = make_badge("UTN FRRo · ISI · TP3", "#312E81", "#C7D2FE")
        hero_lay.addWidget(pill, alignment=Qt.AlignmentFlag.AlignLeft)

        h_title = QLabel("Gestión Integral\nde Shopping")
        h_title.setStyleSheet("font-size: 34px; font-weight: 800; color: #FFFFFF; line-height: 1.15;")
        hero_lay.addWidget(h_title)

        h_desc = QLabel(
            "Administración de locales comerciales, cuentas de dueños, "
            "promociones y reportes de uso en tiempo real sobre los archivos "
            "binarios originales del trabajo práctico."
        )
        h_desc.setWordWrap(True)
        h_desc.setStyleSheet("color: #CBD5E1; font-size: 14px;")
        hero_lay.addWidget(h_desc)

        hero_lay.addSpacing(12)

        # Accesos rápidos de cuentas demo del TP3
        demo_lbl = QLabel("ACCESO RÁPIDO · CUENTAS DE PRUEBA")
        demo_lbl.setObjectName("SectionLabel")
        hero_lay.addWidget(demo_lbl)

        demos = [
            ("Administrador", "admin@shopping.com", "12345", "#6366F1"),
            ("Dueño de Local", "gonzalo@gmail.com", "12345", "#10B981"),
            ("Cliente", "malena@gmail.com", "12345", "#F59E0B"),
        ]
        for role_label, mail, pwd, color in demos:
            btn = QPushButton(f"  {role_label}  ·  {mail}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: rgba(15, 23, 42, 0.75); "
                f"border: 1px solid #334155; border-left: 4px solid {color}; "
                f"border-radius: 9px; text-align: left; padding: 10px 14px; color: #E2E8F0; }}"
                f"QPushButton:hover {{ background-color: #1E293B; }}"
            )
            btn.clicked.connect(lambda _c, m=mail, p=pwd: self._fill_demo(m, p))
            hero_lay.addWidget(btn)

        hero_lay.addStretch()

        credits = QLabel("Gugliermino · Zariaga · García Queipo · López — Comisión 1K6")
        credits.setStyleSheet("color: #94A3B8; font-size: 11px;")
        hero_lay.addWidget(credits)

        # Panel derecho: Tarjeta de Login / Registro
        auth_card = QFrame()
        auth_card.setObjectName("AuthCard")
        auth_card.setMaximumWidth(460)
        auth_card.setMinimumWidth(380)
        card_lay = QVBoxLayout(auth_card)
        card_lay.setContentsMargins(32, 32, 32, 32)
        card_lay.setSpacing(18)

        # Selector Login / Registro
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(8)
        self.btn_tab_login = QPushButton("Iniciar sesión")
        self.btn_tab_reg = QPushButton("Registrarse (Cliente)")
        for b in (self.btn_tab_login, self.btn_tab_reg):
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_login.setChecked(True)
        self.btn_tab_login.clicked.connect(lambda: self._switch_mode(0))
        self.btn_tab_reg.clicked.connect(lambda: self._switch_mode(1))
        toggle_row.addWidget(self.btn_tab_login)
        toggle_row.addWidget(self.btn_tab_reg)
        card_lay.addLayout(toggle_row)

        self.auth_stack = QStackedWidget()
        self.auth_stack.addWidget(self._build_login_form())
        self.auth_stack.addWidget(self._build_register_form())
        card_lay.addWidget(self.auth_stack)

        self._update_toggle_styles(0)

        outer.addWidget(hero, 5)
        outer.addWidget(auth_card, 4)

    def _build_login_form(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.setSpacing(12)

        t = QLabel("Bienvenido de nuevo")
        t.setObjectName("TitleLarge")
        sub = QLabel("Ingresá tus credenciales para acceder al panel.")
        sub.setObjectName("Subtitle")
        lay.addWidget(t)
        lay.addWidget(sub)
        lay.addSpacing(8)

        lay.addWidget(QLabel("Correo electrónico"))
        self.in_login_email = QLineEdit()
        self.in_login_email.setPlaceholderText("usuario@shopping.com")
        lay.addWidget(self.in_login_email)

        lay.addWidget(QLabel("Contraseña"))
        self.in_login_pass = QLineEdit()
        self.in_login_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_login_pass.setPlaceholderText("••••••••")
        self.in_login_pass.returnPressed.connect(self._do_login)
        lay.addWidget(self.in_login_pass)

        self.lbl_login_feedback = QLabel("")
        self.lbl_login_feedback.setWordWrap(True)
        self.lbl_login_feedback.setStyleSheet("color: #F87171; font-size: 12px;")
        lay.addWidget(self.lbl_login_feedback)

        lay.addSpacing(4)
        self.btn_login = QPushButton("Ingresar al sistema")
        self.btn_login.setObjectName("PrimaryBtn")
        self.btn_login.setMinimumHeight(42)
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.clicked.connect(self._do_login)
        lay.addWidget(self.btn_login)

        lay.addStretch()
        return w

    def _build_register_form(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.setSpacing(12)

        t = QLabel("Crear cuenta de Cliente")
        t.setObjectName("TitleLarge")
        sub = QLabel("Registrate para buscar y solicitar descuentos en los locales.")
        sub.setObjectName("Subtitle")
        sub.setWordWrap(True)
        lay.addWidget(t)
        lay.addWidget(sub)
        lay.addSpacing(8)

        lay.addWidget(QLabel("Correo electrónico"))
        self.in_reg_email = QLineEdit()
        self.in_reg_email.setMaxLength(100)
        self.in_reg_email.setPlaceholderText("tu.correo@ejemplo.com")
        lay.addWidget(self.in_reg_email)

        lay.addWidget(QLabel("Contraseña (máximo 8 caracteres)"))
        self.in_reg_pass = QLineEdit()
        self.in_reg_pass.setMaxLength(8)
        self.in_reg_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_reg_pass.setPlaceholderText("Hasta 8 caracteres")
        self.in_reg_pass.returnPressed.connect(self._do_register)
        lay.addWidget(self.in_reg_pass)

        self.lbl_reg_feedback = QLabel("")
        self.lbl_reg_feedback.setWordWrap(True)
        lay.addWidget(self.lbl_reg_feedback)

        btn_reg = QPushButton("Registrarme como Cliente")
        btn_reg.setObjectName("SuccessBtn")
        btn_reg.setMinimumHeight(42)
        btn_reg.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reg.clicked.connect(self._do_register)
        lay.addWidget(btn_reg)

        lay.addStretch()
        return w

    def _switch_mode(self, idx: int) -> None:
        self.auth_stack.setCurrentIndex(idx)
        self._update_toggle_styles(idx)

    def _update_toggle_styles(self, idx: int) -> None:
        self.btn_tab_login.setChecked(idx == 0)
        self.btn_tab_reg.setChecked(idx == 1)
        self.btn_tab_login.setObjectName("PrimaryBtn" if idx == 0 else "GhostBtn")
        self.btn_tab_reg.setObjectName("PrimaryBtn" if idx == 1 else "GhostBtn")
        for b in (self.btn_tab_login, self.btn_tab_reg):
            b.style().unpolish(b)
            b.style().polish(b)

    def _fill_demo(self, mail: str, pwd: str) -> None:
        self._switch_mode(0)
        self.in_login_email.setText(mail)
        self.in_login_pass.setText(pwd)
        self.lbl_login_feedback.setText("")

    def reset_state(self) -> None:
        self.intentos_restantes = 3
        self.in_login_pass.clear()
        self.lbl_login_feedback.clear()
        self.btn_login.setEnabled(True)

    def _do_login(self) -> None:
        ok, msg = self.service.authenticate(
            self.in_login_email.text(), self.in_login_pass.text()
        )
        if ok:
            self.intentos_restantes = 3
            self.lbl_login_feedback.clear()
            self.login_success.emit()
        else:
            self.intentos_restantes -= 1
            if self.intentos_restantes <= 0:
                self.lbl_login_feedback.setText(
                    f"{msg} Se agotaron los 3 intentos permitidos. Reiniciando bloqueo..."
                )
                QMessageBox.critical(
                    self,
                    "Acceso denegado",
                    "Se agotaron los 3 intentos de inicio de sesión.",
                )
                self.intentos_restantes = 3
                self.in_login_pass.clear()
            else:
                self.lbl_login_feedback.setText(
                    f"{msg} Intentos restantes: {self.intentos_restantes}."
                )

    def _do_register(self) -> None:
        ok, msg = self.service.register_user(
            self.in_reg_email.text(), self.in_reg_pass.text(), "cli"
        )
        if ok:
            self.lbl_reg_feedback.setStyleSheet("color: #34D399; font-size: 12px;")
            self.lbl_reg_feedback.setText(msg)
            self.in_login_email.setText(self.in_reg_email.text().strip())
            self.in_login_pass.setText(self.in_reg_pass.text())
            self.in_reg_email.clear()
            self.in_reg_pass.clear()
            QMessageBox.information(self, "Registro exitoso", msg)
            self._switch_mode(0)
        else:
            self.lbl_reg_feedback.setStyleSheet("color: #F87171; font-size: 12px;")
            self.lbl_reg_feedback.setText(msg)


# ---------------------------------------------------------------------------
# Vista compartida: Novedades (Diagramación en Chapin del TP3)
# ---------------------------------------------------------------------------


class NovedadesPage(QWidget):
    def __init__(self, is_admin: bool = False) -> None:
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(16)

        card = QFrame()
        card.setObjectName("Card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(32, 32, 32, 32)
        c_lay.setSpacing(14)

        badge = make_badge("EN CONSTRUCCIÓN · TP3", "#78350F", "#FDE68A")
        c_lay.addWidget(badge, alignment=Qt.AlignmentFlag.AlignHCenter)

        title = QLabel("Diagramación en Chapin")
        title.setObjectName("TitleLarge")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        c_lay.addWidget(title)

        desc = QLabel(
            "En la consigna original del TP3, la sección de Novedades fue modelada "
            "mediante diagramación en Chapin (sin persistencia en disco)."
        )
        desc.setObjectName("Subtitle")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        c_lay.addWidget(desc)

        if is_admin:
            grid = QGridLayout()
            grid.setSpacing(12)
            grid.setColumnStretch(0, 1)
            grid.setColumnStretch(1, 1)
            items = [
                ("a) Crear novedades", "Alta de comunicados y anuncios del shopping."),
                ("b) Modificar novedad", "Edición de vigencia y contenido."),
                ("c) Eliminar novedad", "Baja lógica de novedades publicadas."),
                ("d) Reporte de novedades", "Listado histórico por categoría de usuario."),
            ]
            for i, (h, p) in enumerate(items):
                sub = QFrame()
                sub.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
                )
                sub.setStyleSheet(
                    "background-color: #0B1120; border: 1px solid #1E293B; border-radius: 10px;"
                )
                sl = QVBoxLayout(sub)
                sl.setContentsMargins(16, 14, 16, 14)
                sl.setSpacing(4)
                l1 = QLabel(h)
                l1.setWordWrap(True)
                l1.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
                )
                l1.setStyleSheet("font-weight: 600; color: #E2E8F0;")
                l2 = QLabel(p)
                l2.setWordWrap(True)
                l2.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
                )
                l2.setStyleSheet("color: #94A3B8; font-size: 12px;")
                sl.addWidget(l1)
                sl.addWidget(l2)
                grid.addWidget(sub, i // 2, i % 2)
            c_lay.addSpacing(10)
            c_lay.addLayout(grid)

        lay.addWidget(card)
        lay.addStretch()


# ---------------------------------------------------------------------------
# Páginas de ADMINISTRADOR
# ---------------------------------------------------------------------------


class AdminDashboardPage(QWidget):
    navigate_requested = pyqtSignal(str)

    def __init__(self, service: TP3Service) -> None:
        super().__init__()
        self.service = service
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(18)

        # Fila de KPIs
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)
        c1, self.kpi_locales = make_kpi_card("Locales Activos", "0", "#6366F1")
        c2, self.kpi_espacio = make_kpi_card("Espacios Disponibles", "50", "#10B981")
        c3, self.kpi_pend = make_kpi_card("Promos Pendientes", "0", "#F59E0B")
        c4, self.kpi_usos = make_kpi_card("Usos Registrados", "0", "#EC4899")
        for c in (c1, c2, c3, c4):
            kpi_row.addWidget(c)
        lay.addLayout(kpi_row)

        # Fila inferior: Rubros + Accesos rápidos
        mid = QHBoxLayout()
        mid.setSpacing(16)

        rubro_card = QFrame()
        rubro_card.setObjectName("Card")
        r_lay = QVBoxLayout(rubro_card)
        r_lay.setContentsMargins(20, 18, 20, 18)
        r_lay.setSpacing(12)

        rt = QLabel("Locales Activos por Rubro")
        rt.setObjectName("TitleMedium")
        rs = QLabel("Ordenado dinámicamente mediante ar_orden() del TP3.")
        rs.setObjectName("Subtitle")
        r_lay.addWidget(rt)
        r_lay.addWidget(rs)

        self.tbl_rubros = QTableWidget(3, 2)
        self.tbl_rubros.setHorizontalHeaderLabels(["Rubro", "Cantidad Activa"])
        style_table(self.tbl_rubros)
        self.tbl_rubros.setMaximumHeight(165)
        r_lay.addWidget(self.tbl_rubros)
        r_lay.addStretch()

        quick_card = QFrame()
        quick_card.setObjectName("Card")
        q_lay = QVBoxLayout(quick_card)
        q_lay.setContentsMargins(20, 18, 20, 18)
        q_lay.setSpacing(10)

        qt = QLabel("Acciones Rápidas")
        qt.setObjectName("TitleMedium")
        q_lay.addWidget(qt)

        actions = [
            ("Gestionar Locales y Mapa", "admin_locales", "PrimaryBtn"),
            ("Crear Cuenta de Dueño de Local", "admin_duenos", "GhostBtn"),
            ("Revisar Promociones Pendientes", "admin_promos", "GhostBtn"),
            ("Generar Reporte de Utilización", "admin_reporte", "GhostBtn"),
        ]
        for label, key, obj_name in actions:
            b = QPushButton(label)
            b.setObjectName(obj_name)
            b.setMinimumHeight(40)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _c, k=key: self.navigate_requested.emit(k))
            q_lay.addWidget(b)
        q_lay.addStretch()

        mid.addWidget(rubro_card, 3)
        mid.addWidget(quick_card, 2)
        lay.addLayout(mid)
        lay.addStretch()

    def refresh(self) -> None:
        locales = self.service.get_all_locales()
        activos = sum(1 for l in locales if l.estado == "A")
        promos = self.service.get_all_promociones()
        pendientes = sum(1 for p in promos if p.estado.strip(" ") == "Pendiente")
        usos = len(self.service.get_all_usos())

        self.kpi_locales.setText(str(activos))
        self.kpi_espacio.setText(f"{self.service.get_available_slots()} / 50")
        self.kpi_pend.setText(str(pendientes))
        self.kpi_usos.setText(str(usos))

        stats = self.service.get_rubro_stats()
        self.tbl_rubros.setRowCount(len(stats))
        for i, (rubro, cant) in enumerate(stats):
            self.tbl_rubros.setItem(i, 0, QTableWidgetItem(rubro.capitalize()))
            it = QTableWidgetItem(str(cant))
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_rubros.setItem(i, 1, it)


class AdminLocalesPage(QWidget):
    def __init__(self, service: TP3Service) -> None:
        super().__init__()
        self.service = service
        self._locales_cache: list[Any] = []
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_list_tab(), "Listado y Gestión")
        self.tabs.addTab(self._build_map_tab(), "Mapa de Locales (50 espacios)")
        lay.addWidget(self.tabs)

    def _build_list_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(12)

        # Barra de herramientas
        bar = QHBoxLayout()
        self.in_search = QLineEdit()
        self.in_search.setPlaceholderText("Buscar por nombre, rubro o ubicación...")
        self.in_search.textChanged.connect(self._render_table)

        self.cb_filter_estado = QComboBox()
        self.cb_filter_estado.addItems(["Todos", "Activos (A)", "Dados de baja (B)"])
        self.cb_filter_estado.currentIndexChanged.connect(self._render_table)

        btn_new = QPushButton("+ Nuevo Local")
        btn_new.setObjectName("PrimaryBtn")
        btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new.clicked.connect(self._on_new)

        btn_edit = QPushButton("Modificar")
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.clicked.connect(self._on_edit)

        btn_toggle = QPushButton("Alta / Baja")
        btn_toggle.setObjectName("DangerBtn")
        btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_toggle.clicked.connect(self._on_toggle)

        bar.addWidget(self.in_search, 3)
        bar.addWidget(self.cb_filter_estado, 1)
        bar.addWidget(btn_new)
        bar.addWidget(btn_edit)
        bar.addWidget(btn_toggle)
        lay.addLayout(bar)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Código", "Nombre", "Ubicación", "Rubro", "Dueño", "Estado"]
        )
        style_table(self.table)
        lay.addWidget(self.table)
        return w

    def _build_map_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(14)

        legend = QHBoxLayout()
        legend.addWidget(make_badge("Activo (A)", "#065F46", "#6EE7B7"))
        legend.addWidget(make_badge("Baja (B)", "#7F1D1D", "#FCA5A5"))
        legend.addWidget(make_badge("Disponible", "#1E293B", "#94A3B8"))
        legend.addStretch()
        self.lbl_map_info = QLabel("Hacé clic en un espacio ocupado para ver detalles.")
        self.lbl_map_info.setObjectName("Subtitle")
        legend.addWidget(self.lbl_map_info)
        lay.addLayout(legend)

        card = QFrame()
        card.setObjectName("Card")
        self.map_grid = QGridLayout(card)
        self.map_grid.setContentsMargins(20, 20, 20, 20)
        self.map_grid.setSpacing(8)
        self.map_buttons: list[QPushButton] = []
        for idx in range(50):
            btn = QPushButton("--")
            btn.setMinimumHeight(40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.map_grid.addWidget(btn, idx // 5, idx % 5)
            self.map_buttons.append(btn)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(card)
        lay.addWidget(scroll)
        return w

    def refresh(self) -> None:
        self._locales_cache = self.service.get_all_locales()
        self._render_table()
        self._render_map()

    def _render_table(self) -> None:
        q = self.in_search.text().strip().lower()
        filtro = self.cb_filter_estado.currentIndex()
        users = self.service.get_user_map_by_code()

        filtered = []
        for loc in self._locales_cache:
            if filtro == 1 and loc.estado != "A":
                continue
            if filtro == 2 and loc.estado != "B":
                continue
            blob = f"{loc.codigo} {loc.nombre} {loc.ubicacion} {loc.rubro}".lower()
            if q and q not in blob:
                continue
            filtered.append(loc)

        self.table.setRowCount(len(filtered))
        for row, loc in enumerate(filtered):
            u = users.get(int(loc.codUsuario))
            dueno_txt = f"[{loc.codUsuario}] {u.correo.strip(' ')}" if u else f"[{loc.codUsuario}]"

            it_cod = QTableWidgetItem(loc.codigo)
            it_cod.setData(Qt.ItemDataRole.UserRole, loc.codigo)
            it_cod.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, it_cod)
            self.table.setItem(row, 1, QTableWidgetItem(loc.nombre.strip(" ")))
            self.table.setItem(row, 2, QTableWidgetItem(loc.ubicacion.strip(" ")))
            self.table.setItem(row, 3, QTableWidgetItem(loc.rubro.strip(" ").capitalize()))
            self.table.setItem(row, 4, QTableWidgetItem(dueno_txt))

            badge = (
                make_badge("Activo", "#065F46", "#6EE7B7")
                if loc.estado == "A"
                else make_badge("Baja", "#7F1D1D", "#FCA5A5")
            )
            self.table.setCellWidget(row, 5, badge)

    def _render_map(self) -> None:
        cells = self.service.get_mapa_locales()
        loc_map = self.service.get_local_map_by_code()

        for i, (cod, estado) in enumerate(cells):
            btn = self.map_buttons[i]
            try:
                btn.clicked.disconnect()
            except TypeError:
                pass

            if cod == 0:
                btn.setText("00 · Libre")
                btn.setStyleSheet(
                    "background-color: #0B1120; border: 1px dashed #334155; "
                    "color: #475569; border-radius: 8px; font-weight: 500;"
                )
                btn.clicked.connect(
                    lambda _c, s=i + 1: self.lbl_map_info.setText(f"Espacio #{s}: Disponible.")
                )
            else:
                loc = loc_map.get(cod)
                nom = loc.nombre.strip(" ") if loc else f"Local {cod}"
                cod_fmt = self.service.tp3.convertir_n(cod)
                btn.setText(f"{cod_fmt} · {nom[:12]}")
                if estado == "B":
                    btn.setStyleSheet(
                        "background-color: #450A0A; border: 1px solid #DC2626; "
                        "color: #FECACA; border-radius: 8px; font-weight: 700;"
                    )
                else:
                    btn.setStyleSheet(
                        "background-color: #064E3B; border: 1px solid #10B981; "
                        "color: #D1FAE5; border-radius: 8px; font-weight: 700;"
                    )
                if loc:
                    info = (
                        f"Local [{loc.codigo}] {loc.nombre.strip(' ')} | "
                        f"Rubro: {loc.rubro.strip(' ').capitalize()} | "
                        f"Ubicación: {loc.ubicacion.strip(' ')} | "
                        f"Estado: {'Activo' if loc.estado == 'A' else 'Baja'}"
                    )
                    btn.clicked.connect(lambda _c, txt=info: self.lbl_map_info.setText(txt))

    def _selected_local(self) -> Any | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        cod = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        for loc in self._locales_cache:
            if loc.codigo == cod:
                return loc
        return None

    def _on_new(self) -> None:
        dlg = LocalDialog(self.service, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_edit(self) -> None:
        loc = self._selected_local()
        if loc is None:
            QMessageBox.information(self, "Seleccionar local", "Seleccione un local de la tabla.")
            return
        dlg = LocalDialog(self.service, self, local_obj=loc)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_toggle(self) -> None:
        loc = self._selected_local()
        if loc is None:
            QMessageBox.information(self, "Seleccionar local", "Seleccione un local de la tabla.")
            return
        accion = "dar de baja" if loc.estado == "A" else "reactivar"
        ans = QMessageBox.question(
            self,
            "Confirmar cambio de estado",
            f"¿Desea {accion} el local '{loc.nombre.strip(' ')}' (código {loc.codigo})?",
        )
        if ans == QMessageBox.StandardButton.Yes:
            ok, msg = self.service.toggle_local_estado(loc.codigo)
            if ok:
                QMessageBox.information(self, "Estado actualizado", msg)
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", msg)


class AdminDuenosPage(QWidget):
    def __init__(self, service: TP3Service) -> None:
        super().__init__()
        self.service = service
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(18)

        # Formulario de alta
        form_card = QFrame()
        form_card.setObjectName("Card")
        form_card.setMaximumWidth(380)
        f_lay = QVBoxLayout(form_card)
        f_lay.setContentsMargins(22, 22, 22, 22)
        f_lay.setSpacing(12)

        t = QLabel("Nuevo Dueño de Local")
        t.setObjectName("TitleMedium")
        sub = QLabel("Crea credenciales con rol 'Dueño de local' para asignar locales.")
        sub.setObjectName("Subtitle")
        sub.setWordWrap(True)
        f_lay.addWidget(t)
        f_lay.addWidget(sub)
        f_lay.addSpacing(6)

        f_lay.addWidget(QLabel("Correo electrónico"))
        self.in_email = QLineEdit()
        self.in_email.setMaxLength(100)
        self.in_email.setPlaceholderText("dueno@shopping.com")
        f_lay.addWidget(self.in_email)

        f_lay.addWidget(QLabel("Contraseña (máx. 8 caracteres)"))
        self.in_pass = QLineEdit()
        self.in_pass.setMaxLength(8)
        self.in_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_pass.setPlaceholderText("Hasta 8 caracteres")
        f_lay.addWidget(self.in_pass)

        btn = QPushButton("Crear Cuenta de Dueño")
        btn.setObjectName("PrimaryBtn")
        btn.setMinimumHeight(40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._on_create)
        f_lay.addSpacing(6)
        f_lay.addWidget(btn)
        f_lay.addStretch()

        # Tabla de dueños existentes
        list_card = QFrame()
        list_card.setObjectName("Card")
        l_lay = QVBoxLayout(list_card)
        l_lay.setContentsMargins(20, 20, 20, 20)
        l_lay.setSpacing(10)

        lt = QLabel("Cuentas de Dueños Registradas")
        lt.setObjectName("TitleMedium")
        l_lay.addWidget(lt)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Código", "Correo", "Locales Asignados"])
        style_table(self.table)
        l_lay.addWidget(self.table)

        lay.addWidget(form_card, 2)
        lay.addWidget(list_card, 3)

    def refresh(self) -> None:
        duenos = [
            u for u in self.service.get_all_usuarios() if u.tipo.rstrip(" ") == "Dueno de local"
        ]
        locales = self.service.get_all_locales()
        counts: dict[int, int] = {}
        for loc in locales:
            cid = int(loc.codUsuario)
            counts[cid] = counts.get(cid, 0) + 1

        self.table.setRowCount(len(duenos))
        for i, u in enumerate(duenos):
            c_it = QTableWidgetItem(u.codigo)
            c_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, c_it)
            self.table.setItem(i, 1, QTableWidgetItem(u.correo.strip(" ")))
            cnt = QTableWidgetItem(str(counts.get(int(u.codigo), 0)))
            cnt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 2, cnt)

    def _on_create(self) -> None:
        ok, msg = self.service.register_user(
            self.in_email.text(), self.in_pass.text(), "dueño"
        )
        if ok:
            self.in_email.clear()
            self.in_pass.clear()
            QMessageBox.information(self, "Cuenta creada", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "Validación", msg)


class AdminPromocionesPage(QWidget):
    def __init__(self, service: TP3Service) -> None:
        super().__init__()
        self.service = service
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        bar = QHBoxLayout()
        self.cb_estado = QComboBox()
        self.cb_estado.addItems(["Pendientes", "Todas", "Aprobadas", "Rechazadas"])
        self.cb_estado.currentIndexChanged.connect(self.refresh)

        btn_approve = QPushButton("✓ Aprobar Seleccionada")
        btn_approve.setObjectName("SuccessBtn")
        btn_approve.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_approve.clicked.connect(lambda: self._on_action(True))

        btn_reject = QPushButton("✕ Rechazar Seleccionada")
        btn_reject.setObjectName("DangerBtn")
        btn_reject.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reject.clicked.connect(lambda: self._on_action(False))

        bar.addWidget(QLabel("Filtrar estado:"))
        bar.addWidget(self.cb_estado)
        bar.addStretch()
        bar.addWidget(btn_approve)
        bar.addWidget(btn_reject)
        lay.addLayout(bar)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Cód.", "Local", "Descripción", "Desde", "Hasta", "Días", "Estado"]
        )
        style_table(self.table)
        lay.addWidget(self.table)

    def refresh(self) -> None:
        filtro = self.cb_estado.currentText()
        promos = self.service.get_all_promociones()
        loc_map = self.service.get_local_map_by_code()

        rows = []
        for p in promos:
            est = p.estado.strip(" ")
            if filtro == "Pendientes" and est != "Pendiente":
                continue
            if filtro == "Aprobadas" and est != "Aprobada":
                continue
            if filtro == "Rechazadas" and est != "Rechazada":
                continue
            rows.append(p)

        self.table.setRowCount(len(rows))
        for i, p in enumerate(rows):
            loc = loc_map.get(int(p.codLocal))
            loc_name = f"[{p.codLocal}] {loc.nombre.strip(' ')}" if loc else f"[{p.codLocal}]"
            est = p.estado.strip(" ")

            c_it = QTableWidgetItem(p.codPromo)
            c_it.setData(Qt.ItemDataRole.UserRole, int(p.codPromo))
            c_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(i, 0, c_it)
            self.table.setItem(i, 1, QTableWidgetItem(loc_name))
            self.table.setItem(i, 2, QTableWidgetItem(p.textoPromo.strip(" ")))
            self.table.setItem(i, 3, QTableWidgetItem(p.fechaDesdePromo))
            self.table.setItem(i, 4, QTableWidgetItem(p.fechaHastaPromo))
            self.table.setItem(i, 5, QTableWidgetItem(format_dias(p.diasSemana)))

            colors = {
                "Aprobada": ("#065F46", "#6EE7B7"),
                "Pendiente": ("#78350F", "#FDE68A"),
                "Rechazada": ("#7F1D1D", "#FCA5A5"),
            }
            bg, fg = colors.get(est, ("#1E293B", "#CBD5E1"))
            self.table.setCellWidget(i, 6, make_badge(est, bg, fg))

    def _on_action(self, aprobar: bool) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar promoción", "Seleccione una promoción.")
            return
        cod = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        ok, msg = self.service.update_promocion_estado(cod, aprobar)
        if ok:
            QMessageBox.information(self, "Promoción actualizada", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "No se pudo actualizar", msg)


class ReporteUsosPage(QWidget):
    """Reporte reutilizable para Administrador (todos) y Dueño (sus locales)."""

    def __init__(self, service: TP3Service, solo_dueno: bool = False) -> None:
        super().__init__()
        self.service = service
        self.solo_dueno = solo_dueno
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        filter_card = QFrame()
        filter_card.setObjectName("Card")
        fl = QHBoxLayout(filter_card)
        fl.setContentsMargins(16, 14, 16, 14)
        fl.setSpacing(12)

        self.dt_desde = QDateEdit()
        self.dt_desde.setCalendarPopup(True)
        self.dt_desde.setDisplayFormat("dd/MM/yyyy")
        self.dt_desde.setDate(QDate(2023, 1, 1))

        self.dt_hasta = QDateEdit()
        self.dt_hasta.setCalendarPopup(True)
        self.dt_hasta.setDisplayFormat("dd/MM/yyyy")
        self.dt_hasta.setDate(date_to_qdate(self.service.tp3.fecha_actual))

        btn_run = QPushButton("Generar Reporte")
        btn_run.setObjectName("PrimaryBtn")
        btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_run.clicked.connect(self.refresh)

        btn_demo = QPushButton("Rango Histórico (2023 - Hoy)")
        btn_demo.setObjectName("GhostBtn")
        btn_demo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_demo.clicked.connect(self._preset_all)

        fl.addWidget(QLabel("Desde:"))
        fl.addWidget(self.dt_desde)
        fl.addWidget(QLabel("Hasta:"))
        fl.addWidget(self.dt_hasta)
        fl.addWidget(btn_run)
        fl.addWidget(btn_demo)
        fl.addStretch()
        lay.addWidget(filter_card)

        self.lbl_summary = QLabel("")
        self.lbl_summary.setObjectName("Subtitle")
        lay.addWidget(self.lbl_summary)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Cód. Promo", "Local", "Descripción", "Desde", "Hasta", "Cantidad de Usos"]
        )
        style_table(self.table)
        lay.addWidget(self.table)

    def _preset_all(self) -> None:
        self.dt_desde.setDate(QDate(2023, 1, 1))
        self.dt_hasta.setDate(date_to_qdate(self.service.tp3.fecha_actual))
        self.refresh()

    def refresh(self) -> None:
        f_des = qdate_to_date(self.dt_desde.date())
        f_has = qdate_to_date(self.dt_hasta.date())
        if f_des > f_has:
            QMessageBox.warning(
                self, "Rango inválido", "La fecha inicial debe ser menor o igual a la final."
            )
            return

        rows = self.service.get_reporte_usos(f_des, f_has, solo_dueño=self.solo_dueno)
        total_usos = sum(r["usos"] for r in rows)
        self.lbl_summary.setText(
            f"Promociones aprobadas en el rango: {len(rows)}  ·  Total de usos acumulados: {total_usos}"
        )

        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            c_it = QTableWidgetItem(r["codPromo"])
            c_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            u_it = QTableWidgetItem(str(r["usos"]))
            u_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, c_it)
            self.table.setItem(i, 1, QTableWidgetItem(f"[{r['codLocal']}] {r['nombreLocal']}"))
            self.table.setItem(i, 2, QTableWidgetItem(r["texto"]))
            self.table.setItem(i, 3, QTableWidgetItem(r["desde"]))
            self.table.setItem(i, 4, QTableWidgetItem(r["hasta"]))
            self.table.setItem(i, 5, u_it)


# ---------------------------------------------------------------------------
# Páginas de DUEÑO DE LOCAL
# ---------------------------------------------------------------------------


class DuenoPromocionesPage(QWidget):
    def __init__(self, service: TP3Service) -> None:
        super().__init__()
        self.service = service
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(18)

        # Formulario de nueva promoción
        form_card = QFrame()
        form_card.setObjectName("Card")
        form_card.setMaximumWidth(420)
        fl = QVBoxLayout(form_card)
        fl.setContentsMargins(20, 20, 20, 20)
        fl.setSpacing(10)

        t = QLabel("Crear Descuento")
        t.setObjectName("TitleMedium")
        sub = QLabel("Las nuevas promociones se envían en estado Pendiente para aprobación.")
        sub.setObjectName("Subtitle")
        sub.setWordWrap(True)
        fl.addWidget(t)
        fl.addWidget(sub)

        fl.addWidget(QLabel("Local"))
        self.cb_local = QComboBox()
        fl.addWidget(self.cb_local)

        fl.addWidget(QLabel("Texto descriptivo (máx. 200 caracteres)"))
        self.in_texto = QLineEdit()
        self.in_texto.setMaxLength(200)
        self.in_texto.setPlaceholderText("Ej: 25% OFF abonando con débito")
        fl.addWidget(self.in_texto)

        dates = QHBoxLayout()
        self.dt_desde = QDateEdit()
        self.dt_desde.setCalendarPopup(True)
        self.dt_desde.setDisplayFormat("dd/MM/yyyy")
        self.dt_desde.setDate(date_to_qdate(self.service.tp3.fecha_actual))

        self.dt_hasta = QDateEdit()
        self.dt_hasta.setCalendarPopup(True)
        self.dt_hasta.setDisplayFormat("dd/MM/yyyy")
        self.dt_hasta.setDate(
            date_to_qdate(self.service.tp3.fecha_actual + datetime.timedelta(days=14))
        )

        d1 = QVBoxLayout()
        d1.addWidget(QLabel("Fecha desde"))
        d1.addWidget(self.dt_desde)
        d2 = QVBoxLayout()
        d2.addWidget(QLabel("Fecha hasta"))
        d2.addWidget(self.dt_hasta)
        dates.addLayout(d1)
        dates.addLayout(d2)
        fl.addLayout(dates)

        fl.addWidget(QLabel("Días vigentes"))
        days_row = QHBoxLayout()
        days_row.setSpacing(6)
        self.day_buttons: list[QPushButton] = []
        for label in DAYS_SHORT:
            b = QPushButton(label)
            b.setObjectName("DayPill")
            b.setCheckable(True)
            b.setChecked(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            days_row.addWidget(b)
            self.day_buttons.append(b)
        fl.addLayout(days_row)

        fl.addSpacing(8)
        btn_create = QPushButton("Publicar Solicitud de Descuento")
        btn_create.setObjectName("PrimaryBtn")
        btn_create.setMinimumHeight(40)
        btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_create.clicked.connect(self._on_create)
        fl.addWidget(btn_create)
        fl.addStretch()

        # Tabla de promociones del dueño
        list_card = QFrame()
        list_card.setObjectName("Card")
        ll = QVBoxLayout(list_card)
        ll.setContentsMargins(20, 20, 20, 20)
        ll.setSpacing(10)

        lt = QLabel("Mis Promociones")
        lt.setObjectName("TitleMedium")
        ll.addWidget(lt)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Cód.", "Local", "Descripción", "Vigencia", "Días", "Estado"]
        )
        style_table(self.table)
        ll.addWidget(self.table)

        lay.addWidget(form_card, 2)
        lay.addWidget(list_card, 3)

    def refresh(self) -> None:
        self.cb_local.clear()
        my_locales = self.service.get_owner_locales()
        for loc in my_locales:
            if loc.estado == "A":
                self.cb_local.addItem(
                    f"[{loc.codigo}] {loc.nombre.strip(' ')}", int(loc.codigo)
                )

        promos = self.service.get_owner_promociones()
        loc_map = self.service.get_local_map_by_code()
        self.table.setRowCount(len(promos))
        for i, p in enumerate(promos):
            loc = loc_map.get(int(p.codLocal))
            loc_name = loc.nombre.strip(" ") if loc else p.codLocal
            est = p.estado.strip(" ")

            c_it = QTableWidgetItem(p.codPromo)
            c_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, c_it)
            self.table.setItem(i, 1, QTableWidgetItem(f"[{p.codLocal}] {loc_name}"))
            self.table.setItem(i, 2, QTableWidgetItem(p.textoPromo.strip(" ")))
            self.table.setItem(
                i, 3, QTableWidgetItem(f"{p.fechaDesdePromo} → {p.fechaHastaPromo}")
            )
            self.table.setItem(i, 4, QTableWidgetItem(format_dias(p.diasSemana)))

            colors = {
                "Aprobada": ("#065F46", "#6EE7B7"),
                "Pendiente": ("#78350F", "#FDE68A"),
                "Rechazada": ("#7F1D1D", "#FCA5A5"),
            }
            bg, fg = colors.get(est, ("#1E293B", "#CBD5E1"))
            self.table.setCellWidget(i, 5, make_badge(est, bg, fg))

    def _on_create(self) -> None:
        if self.cb_local.count() == 0:
            QMessageBox.warning(
                self, "Sin locales activos", "No tenés locales activos asignados."
            )
            return
        cod_loc = self.cb_local.currentData()
        dias = [1 if b.isChecked() else 0 for b in self.day_buttons]
        ok, msg = self.service.create_promocion(
            cod_loc,
            self.in_texto.text(),
            qdate_to_date(self.dt_desde.date()),
            qdate_to_date(self.dt_hasta.date()),
            dias,
        )
        if ok:
            self.in_texto.clear()
            QMessageBox.information(self, "Descuento creado", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "Validación", msg)


# ---------------------------------------------------------------------------
# Páginas de CLIENTE
# ---------------------------------------------------------------------------


class ClienteBuscarPage(QWidget):
    redeemed = pyqtSignal()

    def __init__(self, service: TP3Service) -> None:
        super().__init__()
        self.service = service
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        card = QFrame()
        card.setObjectName("Card")
        fl = QHBoxLayout(card)
        fl.setContentsMargins(16, 14, 16, 14)
        fl.setSpacing(12)

        self.cb_local = QComboBox()
        self.cb_local.setMinimumWidth(220)

        self.dt_fecha = QDateEdit()
        self.dt_fecha.setCalendarPopup(True)
        self.dt_fecha.setDisplayFormat("dd/MM/yyyy")
        self.dt_fecha.setDate(date_to_qdate(self.service.tp3.fecha_actual))

        btn_search = QPushButton("Buscar Descuentos")
        btn_search.setObjectName("PrimaryBtn")
        btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_search.clicked.connect(self._do_search)

        fl.addWidget(QLabel("Local:"))
        fl.addWidget(self.cb_local)
        fl.addWidget(QLabel("Fecha:"))
        fl.addWidget(self.dt_fecha)
        fl.addWidget(btn_search)
        fl.addStretch()
        lay.addWidget(card)

        self.lbl_info = QLabel("Seleccioná un local y una fecha para consultar promociones aprobadas.")
        self.lbl_info.setObjectName("Subtitle")
        lay.addWidget(self.lbl_info)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Cód. Promo", "Descripción", "Desde", "Hasta", "Acción"]
        )
        style_table(self.table)
        lay.addWidget(self.table)

    def refresh(self) -> None:
        current_data = self.cb_local.currentData()
        self.cb_local.clear()
        for loc in self.service.get_all_locales():
            if loc.estado == "A":
                self.cb_local.addItem(
                    f"[{loc.codigo}] {loc.nombre.strip(' ')} ({loc.rubro.strip(' ')})",
                    loc.codigo,
                )
        if current_data is not None:
            idx = self.cb_local.findData(current_data)
            if idx >= 0:
                self.cb_local.setCurrentIndex(idx)
        self._do_search()

    def _do_search(self) -> None:
        if self.cb_local.count() == 0:
            self.table.setRowCount(0)
            self.lbl_info.setText("No hay locales activos disponibles.")
            return

        cod_local = self.cb_local.currentData()
        fecha = qdate_to_date(self.dt_fecha.date())
        matches = self.service.search_promociones_cliente(cod_local, fecha)

        self.lbl_info.setText(
            f"Se encontraron {len(matches)} promociones vigentes para el {fecha.strftime('%d/%m/%Y')}."
        )
        self.table.setRowCount(len(matches))
        for i, p in enumerate(matches):
            c_it = QTableWidgetItem(p.codPromo)
            c_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, c_it)
            self.table.setItem(i, 1, QTableWidgetItem(p.textoPromo.strip(" ")))
            self.table.setItem(i, 2, QTableWidgetItem(p.fechaDesdePromo))
            self.table.setItem(i, 3, QTableWidgetItem(p.fechaHastaPromo))

            btn = QPushButton("Solicitar ahora")
            btn.setObjectName("SuccessBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _c, cod=int(p.codPromo): self._redeem(cod))
            self.table.setCellWidget(i, 4, btn)

    def _redeem(self, cod_promo: int) -> None:
        ok, msg = self.service.redeem_promocion(cod_promo)
        if ok:
            QMessageBox.information(self, "Descuento solicitado", msg)
            self.redeemed.emit()
        else:
            QMessageBox.warning(self, "No disponible hoy", msg)


class ClienteSolicitarPage(QWidget):
    def __init__(self, service: TP3Service) -> None:
        super().__init__()
        self.service = service
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(16)

        # Card de canje rápido por código
        redeem_card = QFrame()
        redeem_card.setObjectName("Card")
        rl = QHBoxLayout(redeem_card)
        rl.setContentsMargins(20, 18, 20, 18)
        rl.setSpacing(12)

        self.in_cod = QLineEdit()
        self.in_cod.setPlaceholderText("Ingresá el código de promoción (ej: 01, 04...)")
        self.in_cod.setMaximumWidth(280)
        self.in_cod.returnPressed.connect(self._on_redeem)

        btn = QPushButton("Canjear Descuento")
        btn.setObjectName("SuccessBtn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._on_redeem)

        rl.addWidget(QLabel("Código de Promoción:"))
        rl.addWidget(self.in_cod)
        rl.addWidget(btn)
        rl.addStretch()
        lay.addWidget(redeem_card)

        # Historial de usos del cliente actual
        hist_lbl = QLabel("Mi Historial de Descuentos Utilizados")
        hist_lbl.setObjectName("TitleMedium")
        lay.addWidget(hist_lbl)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Cód. Promo", "Local", "Descripción", "Fecha de Uso"]
        )
        style_table(self.table)
        lay.addWidget(self.table)

    def refresh(self) -> None:
        cod_cli = self.service.tp3.busqUsuarioActual()
        usos = [u for u in self.service.get_all_usos() if int(u.codCliente) == cod_cli]
        promos = {int(p.codPromo): p for p in self.service.get_all_promociones()}
        locales = self.service.get_local_map_by_code()

        self.table.setRowCount(len(usos))
        for i, u in enumerate(usos):
            p = promos.get(int(u.codPromo))
            loc_name = "-"
            desc = "-"
            if p:
                desc = p.textoPromo.strip(" ")
                loc = locales.get(int(p.codLocal))
                loc_name = loc.nombre.strip(" ") if loc else p.codLocal

            c_it = QTableWidgetItem(u.codPromo)
            c_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, c_it)
            self.table.setItem(i, 1, QTableWidgetItem(loc_name))
            self.table.setItem(i, 2, QTableWidgetItem(desc))
            self.table.setItem(i, 3, QTableWidgetItem(u.fechaUsoPromo))

    def _on_redeem(self) -> None:
        raw = self.in_cod.text().strip()
        if not raw.isdigit():
            QMessageBox.warning(self, "Código inválido", "Ingrese un código numérico.")
            return
        ok, msg = self.service.redeem_promocion(int(raw))
        if ok:
            self.in_cod.clear()
            QMessageBox.information(self, "Descuento aplicado", msg)
            self.refresh()
        else:
            QMessageBox.warning(self, "Validación", msg)


# ---------------------------------------------------------------------------
# Shell Principal de la Aplicación (Sidebar + TopBar + Páginas por Rol)
# ---------------------------------------------------------------------------


class MainDashboard(QWidget):
    logout_requested = pyqtSignal()

    def __init__(self, service: TP3Service) -> None:
        super().__init__()
        self.service = service
        self.pages: dict[str, tuple[str, str, QWidget]] = {}
        self.nav_buttons: dict[str, QPushButton] = {}
        self._build_shell()

    def _build_shell(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(250)
        sb_lay = QVBoxLayout(sidebar)
        sb_lay.setContentsMargins(16, 20, 16, 20)
        sb_lay.setSpacing(10)

        brand = QLabel("Shopping Gestión")
        brand.setStyleSheet("font-size: 18px; font-weight: 800; color: #FFFFFF;")
        sb_lay.addWidget(brand)

        self.lbl_role_badge = make_badge("ROL", "#312E81", "#C7D2FE")
        sb_lay.addWidget(self.lbl_role_badge, alignment=Qt.AlignmentFlag.AlignLeft)

        sb_lay.addSpacing(8)
        self.nav_container = QVBoxLayout()
        self.nav_container.setSpacing(4)
        sb_lay.addLayout(self.nav_container)
        sb_lay.addStretch()

        # Info de usuario actual
        user_box = QFrame()
        user_box.setStyleSheet(
            "background-color: #111C33; border: 1px solid #1E293B; border-radius: 10px;"
        )
        u_lay = QVBoxLayout(user_box)
        u_lay.setContentsMargins(12, 10, 12, 10)
        u_lay.setSpacing(2)
        self.lbl_user_mail = QLabel("")
        self.lbl_user_mail.setStyleSheet("font-weight: 600; font-size: 12px; color: #F8FAFC;")
        self.lbl_user_code = QLabel("")
        self.lbl_user_code.setStyleSheet("font-size: 11px; color: #94A3B8;")
        u_lay.addWidget(self.lbl_user_mail)
        u_lay.addWidget(self.lbl_user_code)
        sb_lay.addWidget(user_box)

        btn_logout = QPushButton("Cerrar sesión")
        btn_logout.setObjectName("GhostBtn")
        btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.clicked.connect(self.logout_requested.emit)
        sb_lay.addWidget(btn_logout)

        # Área principal
        right = QWidget()
        r_lay = QVBoxLayout(right)
        r_lay.setContentsMargins(0, 0, 0, 0)
        r_lay.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("TopBar")
        tb_lay = QHBoxLayout(topbar)
        tb_lay.setContentsMargins(24, 14, 24, 14)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.lbl_page_title = QLabel("Panel")
        self.lbl_page_title.setObjectName("TitleMedium")
        self.lbl_page_sub = QLabel("")
        self.lbl_page_sub.setObjectName("Subtitle")
        title_col.addWidget(self.lbl_page_title)
        title_col.addWidget(self.lbl_page_sub)

        tb_lay.addLayout(title_col)
        tb_lay.addStretch()

        fecha_str = self.service.tp3.fecha_actual.strftime("%d/%m/%Y")
        tb_lay.addWidget(make_badge(f"Hoy: {fecha_str}", "#1E293B", "#CBD5E1"))

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.setObjectName("GhostBtn")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.clicked.connect(self.refresh_current)
        tb_lay.addWidget(btn_refresh)

        self.stack = QStackedWidget()
        content_wrap = QWidget()
        cw_lay = QVBoxLayout(content_wrap)
        cw_lay.setContentsMargins(24, 20, 24, 20)
        cw_lay.addWidget(self.stack)

        r_lay.addWidget(topbar)
        r_lay.addWidget(content_wrap, 1)

        root.addWidget(sidebar)
        root.addWidget(right, 1)

    def load_for_current_user(self) -> None:
        user = self.service.current_user
        if not user:
            return

        # Limpiar navegación y páginas previas
        while self.nav_container.count():
            item = self.nav_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()
        self.pages.clear()
        self.nav_buttons.clear()

        self.lbl_user_mail.setText(user["correo"])
        self.lbl_user_code.setText(f"Código de usuario: {user['codigo']}")

        role = user["tipo"]
        if role == "administrador":
            self.lbl_role_badge.setText("ADMINISTRADOR")
            self.lbl_role_badge.setStyleSheet(
                "background-color: #312E81; color: #C7D2FE; border-radius: 10px; "
                "padding: 3px 10px; font-size: 11px; font-weight: 700;"
            )
            dash = AdminDashboardPage(self.service)
            dash.navigate_requested.connect(self.select_page)
            self._add_page("admin_dash", "Resumen General", "Métricas del shopping en tiempo real", dash)
            self._add_page("admin_locales", "Gestión de Locales", "Alta, baja, modificación y mapa de 50 espacios", AdminLocalesPage(self.service))
            self._add_page("admin_duenos", "Dueños de Locales", "Creación y consulta de cuentas de dueños", AdminDuenosPage(self.service))
            self._add_page("admin_promos", "Aprobar Promociones", "Revisar, aprobar o rechazar solicitudes de descuento", AdminPromocionesPage(self.service))
            self._add_page("admin_reporte", "Reporte de Usos", "Utilización de descuentos aprobados por rango de fechas", ReporteUsosPage(self.service, solo_dueno=False))
            self._add_page("admin_novedades", "Gestión de Novedades", "Módulo de novedades del TP3", NovedadesPage(is_admin=True))
            self.select_page("admin_dash")

        elif role == "Dueno de local":
            self.lbl_role_badge.setText("DUEÑO DE LOCAL")
            self.lbl_role_badge.setStyleSheet(
                "background-color: #064E3B; color: #A7F3D0; border-radius: 10px; "
                "padding: 3px 10px; font-size: 11px; font-weight: 700;"
            )
            self._add_page("dueno_promos", "Descuentos y Promos", "Creá promociones y consultá su estado", DuenoPromocionesPage(self.service))
            self._add_page("dueno_reporte", "Reporte de Usos", "Rendimiento de tus promociones aprobadas", ReporteUsosPage(self.service, solo_dueno=True))
            self._add_page("dueno_novedades", "Ver Novedades", "Novedades para dueños de locales", NovedadesPage(is_admin=False))
            self.select_page("dueno_promos")

        else:
            self.lbl_role_badge.setText("CLIENTE")
            self.lbl_role_badge.setStyleSheet(
                "background-color: #78350F; color: #FDE68A; border-radius: 10px; "
                "padding: 3px 10px; font-size: 11px; font-weight: 700;"
            )
            buscar_pg = ClienteBuscarPage(self.service)
            solicitar_pg = ClienteSolicitarPage(self.service)
            buscar_pg.redeemed.connect(solicitar_pg.refresh)
            self._add_page("cli_buscar", "Buscar Descuentos", "Consultá promociones aprobadas por local y fecha", buscar_pg)
            self._add_page("cli_solicitar", "Solicitar Descuento", "Canjeá un código vigente hoy y revisá tu historial", solicitar_pg)
            self._add_page("cli_novedades", "Ver Novedades", "Novedades para clientes del shopping", NovedadesPage(is_admin=False))
            self.select_page("cli_buscar")

    def _add_page(self, key: str, title: str, subtitle: str, widget: QWidget) -> None:
        self.pages[key] = (title, subtitle, widget)
        self.stack.addWidget(widget)

        btn = QPushButton(title)
        btn.setObjectName("NavBtn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda _c, k=key: self.select_page(k))
        self.nav_container.addWidget(btn)
        self.nav_buttons[key] = btn

    def select_page(self, key: str) -> None:
        if key not in self.pages:
            return
        title, subtitle, widget = self.pages[key]
        self.lbl_page_title.setText(title)
        self.lbl_page_sub.setText(subtitle)
        self.stack.setCurrentWidget(widget)

        for k, btn in self.nav_buttons.items():
            btn.setProperty("active", k == key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if hasattr(widget, "refresh"):
            widget.refresh()

    def refresh_current(self) -> None:
        w = self.stack.currentWidget()
        if w is not None and hasattr(w, "refresh"):
            w.refresh()


# ---------------------------------------------------------------------------
# Ventana Principal
# ---------------------------------------------------------------------------


class ShoppingAppWindow(QMainWindow):
    def __init__(self, service: TP3Service) -> None:
        super().__init__()
        self.service = service
        self.setWindowTitle("Shopping Gestión · TP3 (PyQt6)")
        self.resize(1180, 740)
        self.setMinimumSize(960, 620)

        root = QWidget()
        root.setObjectName("RootWidget")
        lay = QVBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)

        self.root_stack = QStackedWidget()
        self.auth_screen = AuthScreen(service)
        self.dashboard = MainDashboard(service)

        self.auth_screen.login_success.connect(self._on_login)
        self.dashboard.logout_requested.connect(self._on_logout)

        self.root_stack.addWidget(self.auth_screen)
        self.root_stack.addWidget(self.dashboard)
        lay.addWidget(self.root_stack)

        self.setCentralWidget(root)

    def _on_login(self) -> None:
        self.dashboard.load_for_current_user()
        self.root_stack.setCurrentWidget(self.dashboard)

    def _on_logout(self) -> None:
        self.service.logout()
        self.auth_screen.reset_state()
        self.root_stack.setCurrentWidget(self.auth_screen)


def main() -> int:
    tp3 = load_tp3_module()
    service = TP3Service(tp3)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    app.aboutToQuit.connect(service.close)

    win = ShoppingAppWindow(service)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
