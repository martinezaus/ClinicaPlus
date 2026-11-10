import ctypes
import sys
from ctypes import wintypes


class ImpresionError(Exception):
    pass


def _zpl_field(value):
    encoded = str(value).encode("utf-8")
    return "".join(f"\\{byte:02X}" for byte in encoded)


def _tspl_field(value):
    text = " ".join(str(value).split())
    text = text.replace('"', "”")
    return text.encode("cp1252", errors="replace").decode("cp1252")


def _mm(value):
    return f"{float(value):.1f}"


def _rows(data):
    rows = [
        (data["apellido_nombre"], True),
        (f"DNI {data['documento']}", False),
        (f"Nac. {data['fecha_nacimiento']:%d/%m/%Y}", False),
    ]
    if data.get("historia_clinica"):
        rows.append((f"HC {data['historia_clinica']}", False))
    rows.append((data["servicio"], False))
    if data.get("alergias"):
        rows.append((f"ALERGIA: {data['alergias']}", True))
    return rows


def construir_zpl(data, perfil, copias):
    dpi = perfil.impresora.dpi
    dots_per_mm = dpi / 25.4
    width = round(float(perfil.ancho_mm) * dots_per_mm)
    length = round(float(perfil.largo_mm) * dots_per_mm)
    margin = max(4, round(width * 0.035))
    gap = round(float(perfil.desplazamiento_mm) * dots_per_mm)
    commands = [
        "^XA",
        f"^PW{width}",
        f"^LL{length}",
        {"gap": "^MNY", "black_mark": "^MNM", "continuous": "^MNN"}[perfil.sensor],
        f"^MD{perfil.oscuridad}",
        f"^PR{perfil.velocidad}",
        f"^LT{gap}",
        "^CI28",
    ]

    if perfil.rotacion == 90:
        row_x = margin
        row_y = margin
        for value, bold in _rows(data):
            font = max(12, round(width * (0.12 if bold else 0.085)))
            commands.append(
                f"^FO{row_x},{row_y}^A0R,{font},{font}"
                f"^FH\\^FD{_zpl_field(value)}^FS"
            )
            row_x += font + max(3, round(width * 0.025))
    else:
        row_y = margin
        for value, bold in _rows(data):
            font = max(12, round(width * (0.12 if bold else 0.085)))
            commands.append(
                f"^FO{margin},{row_y}^A0N,{font},{font}"
                f"^FH\\^FD{_zpl_field(value)}^FS"
            )
            row_y += font + max(3, round(width * 0.025))

    commands.extend((f"^PQ{copias}", "^XZ"))
    return "".join(commands).encode("ascii")


def construir_tspl(data, perfil, copias):
    dpi = perfil.impresora.dpi
    dots_per_mm = dpi / 25.4
    width = round(float(perfil.ancho_mm) * dots_per_mm)
    margin = max(4, round(width * 0.035))
    rotation = perfil.rotacion
    lines = [
        f"SIZE {_mm(perfil.ancho_mm)} mm,{_mm(perfil.largo_mm)} mm",
        "DIRECTION 1",
        f"SPEED {perfil.velocidad}",
        f"DENSITY {perfil.oscuridad}",
        f"OFFSET {_mm(perfil.desplazamiento_mm)} mm",
    ]
    if perfil.sensor == "gap":
        lines.append(f"GAP {_mm(perfil.separacion_mm)} mm,0")
    elif perfil.sensor == "black_mark":
        lines.append(f"BLINE {_mm(perfil.separacion_mm)} mm,0")
    else:
        lines.append("GAP 0 mm,0")
    lines.extend(("CODEPAGE 1252", "CLS"))

    if rotation == 90:
        x = margin
        y = margin
        for value, bold in _rows(data):
            scale = 2 if bold else 1
            lines.append(
                f'TEXT {x},{y},"0",{rotation},{scale},{scale},"{_tspl_field(value)}"'
            )
            x += round(16 * scale + width * 0.025)
    else:
        x = margin
        y = margin
        for value, bold in _rows(data):
            scale = 2 if bold else 1
            lines.append(
                f'TEXT {x},{y},"0",{rotation},{scale},{scale},"{_tspl_field(value)}"'
            )
            y += round(16 * scale + width * 0.025)

    lines.extend((f"PRINT 1,{copias}", ""))
    return "\r\n".join(lines).encode("cp1252", errors="replace")


def construir_comando(data, perfil, copias):
    if perfil.impresora.driver == "zpl":
        return construir_zpl(data, perfil, copias)
    if perfil.impresora.driver == "tspl":
        return construir_tspl(data, perfil, copias)
    raise ImpresionError("El protocolo configurado para esta impresora no es compatible.")


def enviar_a_windows(cola_sistema, payload):
    if sys.platform != "win32":
        raise ImpresionError(
            "La impresión USB directa requiere que Django se ejecute en Windows, "
            "en el equipo donde está instalada la impresora."
        )
    if not cola_sistema.strip():
        raise ImpresionError("Falta configurar el nombre de la impresora en Windows.")

    class DocInfo1W(ctypes.Structure):
        _fields_ = [
            ("pDocName", wintypes.LPWSTR),
            ("pOutputFile", wintypes.LPWSTR),
            ("pDatatype", wintypes.LPWSTR),
        ]

    winspool = ctypes.WinDLL("winspool.drv", use_last_error=True)
    winspool.OpenPrinterW.argtypes = [
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.LPVOID,
    ]
    winspool.OpenPrinterW.restype = wintypes.BOOL
    winspool.StartDocPrinterW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPVOID,
    ]
    winspool.StartDocPrinterW.restype = wintypes.DWORD
    winspool.StartPagePrinter.argtypes = [wintypes.HANDLE]
    winspool.StartPagePrinter.restype = wintypes.BOOL
    winspool.WritePrinter.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    winspool.WritePrinter.restype = wintypes.BOOL
    winspool.EndPagePrinter.argtypes = [wintypes.HANDLE]
    winspool.EndPagePrinter.restype = wintypes.BOOL
    winspool.EndDocPrinter.argtypes = [wintypes.HANDLE]
    winspool.EndDocPrinter.restype = wintypes.BOOL
    winspool.ClosePrinter.argtypes = [wintypes.HANDLE]
    winspool.ClosePrinter.restype = wintypes.BOOL
    printer_handle = wintypes.HANDLE()
    if not winspool.OpenPrinterW(
        cola_sistema,
        ctypes.byref(printer_handle),
        None,
    ):
        raise ImpresionError(
            f"No se pudo abrir la impresora «{cola_sistema}»: "
            f"{ctypes.WinError(ctypes.get_last_error())}"
        )

    document_started = False
    page_started = False
    try:
        document = DocInfo1W("Pulsera identificatoria", None, "RAW")
        if not winspool.StartDocPrinterW(
            printer_handle,
            1,
            ctypes.cast(ctypes.byref(document), wintypes.LPVOID),
        ):
            raise ImpresionError(
                f"No se pudo iniciar el trabajo de impresión: "
                f"{ctypes.WinError(ctypes.get_last_error())}"
            )
        document_started = True
        if not winspool.StartPagePrinter(printer_handle):
            raise ImpresionError(
                f"No se pudo iniciar la página de impresión: "
                f"{ctypes.WinError(ctypes.get_last_error())}"
            )
        page_started = True
        buffer = ctypes.create_string_buffer(payload)
        written = wintypes.DWORD()
        if not winspool.WritePrinter(
            printer_handle,
            ctypes.cast(buffer, ctypes.POINTER(wintypes.BYTE)),
            len(payload),
            ctypes.byref(written),
        ):
            raise ImpresionError(
                f"No se pudieron enviar los datos a la impresora: "
                f"{ctypes.WinError(ctypes.get_last_error())}"
            )
        if written.value != len(payload):
            raise ImpresionError("Windows no confirmó el envío completo del trabajo.")
        if not winspool.EndPagePrinter(printer_handle):
            raise ImpresionError("No se pudo cerrar la página de impresión.")
        page_started = False
        if not winspool.EndDocPrinter(printer_handle):
            raise ImpresionError("No se pudo finalizar el trabajo de impresión.")
        document_started = False
    finally:
        if page_started:
            winspool.EndPagePrinter(printer_handle)
        if document_started:
            winspool.EndDocPrinter(printer_handle)
        winspool.ClosePrinter(printer_handle)
