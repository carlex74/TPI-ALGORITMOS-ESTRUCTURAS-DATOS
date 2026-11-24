# TRABAJO PRÁCTICO INTEGRADOR - Gestión de Locales (Shopping)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-6.12-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![Colorama](https://img.shields.io/badge/CLI-Colorama-F59E0B?style=for-the-badge)
![UTN FRRo](https://img.shields.io/badge/UTN%20FRRo-ISI%20%C2%B7%201K6-6366F1?style=for-the-badge)
![UI + CLI](https://img.shields.io/badge/Interfaz-Desktop%20UI%20%2B%20Terminal-10B981?style=for-the-badge)

Este trabajo fue hecho para la materia Algoritmos y Estructuras de Datos de 1er año de la carrera de Ingeniería en Sistemas de Información (ISI) de la Universidad Tecnológica Nacional (U.T.N.) Regional Rosario.

---

## Contexto

La consigna del TP se basaba en un caso real en el que se desarrolló un software para administrar un shopping de Rosario.

La consigna, por obvias razones, era un recorte acotado a la gestión de locales, clientes, usuarios, promociones y reportes de utilización.

## Recuperación del TP

Este trabajo fue realizado por **Evelyn López**, **Teo García Queipo**, **Franco Zariaga** y **Carlo Gugliermino** (Comisión 1K6).

Principalmente se logró recuperar el TP dado que cuando fue desarrollado originalmente no se utilizó GitHub de una manera eficiente para gestionar las versiones.

Además, se añade una **interfaz gráfica moderna en PyQt6** (`app_ui.py`) pensada para que quien clone el repositorio pueda utilizar el sistema cómodamente sin necesidad de ejecutarlo únicamente por terminal, consumiendo directamente las funciones, estructuras y archivos binarios (`db/*.dat`) del archivo original sin modificarlo.

---

## Instalación del entorno virtual (`venv`) y ejecución

Se recomienda crear un entorno virtual (`.venv`) para aislar las dependencias del proyecto (`PyQt6` y `colorama`, listadas en `requirements.txt`).

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd TP3-Gugliermino-Zariaga-Garcia-Lopez
```

### 2. Crear y activar el entorno virtual

#### En Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> Si PowerShell bloquea la ejecución de scripts, podés habilitarlo para la sesión actual con:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`

#### En Windows (CMD)

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

#### En Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar las dependencias

Con el entorno virtual activado:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación

- **Interfaz gráfica moderna (PyQt6):**

  ```bash
  python app_ui.py
  ```

  *(O directamente en Windows sin activar el entorno: `.\.venv\Scripts\python.exe app_ui.py`)*

- **Versión original por terminal (CLI):**

  ```bash
  python "TP3-Gugliermino-Zariaga-Garcia-Lopez .py"
  ```

---

## Cuentas de prueba incluidas en `db/usuarios.dat`

La interfaz de inicio de sesión incluye accesos rápidos para probar cada rol con los datos precargados:

| Rol | Correo | Contraseña |
| :--- | :--- | :--- |
| **Administrador** | `admin@shopping.com` | `12345` |
| **Dueño de local** | `gonzalo@gmail.com` | `12345` |
| **Dueño de local** | `carmen@gmail.com` | `1234` |
| **Cliente** | `malena@gmail.com` | `12345` |
| **Cliente** | `ricardo@gmail.com` | `1234` |

---

## Funcionalidades por rol

- **Administrador**: Resumen general con métricas y conteo de locales por rubro, alta/modificación/baja lógica de locales, mapa visual de los 50 espacios del shopping, creación de cuentas para dueños, aprobación/rechazo de promociones y reporte de utilización por rango de fechas.
- **Dueño de local**: Creación de solicitudes de descuento con selector de vigencia y días de la semana, seguimiento de estado (`Pendiente`, `Aprobada`, `Rechazada`) y reporte de uso de sus locales.
- **Cliente**: Registro de nuevos clientes, búsqueda de descuentos aprobados por local y fecha, canje de promociones por código e historial de usos.
- **Novedades**: Modelada originalmente mediante *Diagramación en Chapin* según la consigna del TP3.

## Estructura del proyecto

```text
TP3-Gugliermino-Zariaga-Garcia-Lopez/
├── TP3-Gugliermino-Zariaga-Garcia-Lopez .py   # Código original del TP3 (intacto)
├── app_ui.py                                  # Interfaz gráfica moderna en PyQt6
├── requirements.txt                           # Dependencias del proyecto
├── db/                                        # Archivos binarios pickle originales (.dat)
└── README.md
```
