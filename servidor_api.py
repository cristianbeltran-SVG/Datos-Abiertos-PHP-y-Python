"""
Módulo adicional de la actividad SENA.
API REST creada con Python estándar: no utiliza Flask ni librerías externas.
Ejecutar con: python servidor_api.py
Luego abrir: http://127.0.0.1:5000
"""

import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


# Se usan las mismas áreas aproximadas que en la consulta PHP.
LOCALIDADES = {
    "Usaquén": "-74.100,4.680,-74.000,4.840",
    "Chapinero": "-74.100,4.620,-74.030,4.710",
    "Santa Fe": "-74.130,4.530,-74.030,4.650",
    "San Cristóbal": "-74.130,4.500,-74.020,4.620",
    "Usme": "-74.220,4.420,-74.070,4.580",
    "Tunjuelito": "-74.170,4.550,-74.100,4.620",
    "Bosa": "-74.220,4.580,-74.130,4.680",
    "Kennedy": "-74.200,4.570,-74.090,4.670",
    "Fontibón": "-74.190,4.620,-74.100,4.710",
    "Engativá": "-74.160,4.650,-74.080,4.740",
    "Suba": "-74.150,4.700,-74.020,4.840",
    "Barrios Unidos": "-74.100,4.650,-74.050,4.690",
    "Teusaquillo": "-74.100,4.610,-74.050,4.660",
    "Los Mártires": "-74.110,4.590,-74.060,4.630",
    "Antonio Nariño": "-74.130,4.560,-74.080,4.610",
    "Puente Aranda": "-74.150,4.580,-74.080,4.650",
    "La Candelaria": "-74.090,4.570,-74.050,4.610",
    "Rafael Uribe Uribe": "-74.140,4.530,-74.070,4.600",
    "Ciudad Bolívar": "-74.230,4.450,-74.080,4.590",
    "Sumapaz": "-74.450,3.950,-74.050,4.550",
}

URL_BASE = (
    "https://services2.arcgis.com/NEwhEo9GGSHXcRXV/arcgis/rest/services/"
    "Paraderos_SITP_Bogot%C3%A1_D_C/FeatureServer/0/query?"
)
FUENTE = "https://datosabiertos.bogota.gov.co/dataset/paraderos-sitp-bogota-d-c"


def consultar_arcgis(localidad):
    """Consulta ArcGIS y construye un indicador con total y muestra de cinco paraderos."""
    datos_comunes = {
        "where": "1=1",
        "geometry": LOCALIDADES[localidad],
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "inSR": 4326,
    }

    # Primera consulta: ArcGIS devuelve solamente la cantidad exacta de resultados.
    parametros_total = {**datos_comunes, "returnCountOnly": "true", "f": "json"}
    total = descargar_json(URL_BASE + urlencode(parametros_total)).get("count", 0)

    # Segunda consulta: se obtiene una muestra útil para visualizar el indicador.
    parametros_muestra = {
        **datos_comunes,
        "outFields": "NTRCODIGO,NTRNOMBRE,NTRDIRECCION",
        "returnGeometry": "true",
        "resultRecordCount": 5,
        "f": "geojson",
    }
    respuesta = descargar_json(URL_BASE + urlencode(parametros_muestra))
    muestra = []
    for elemento in respuesta.get("features", []):
        propiedades = elemento.get("properties", {})
        coordenadas = elemento.get("geometry", {}).get("coordinates", [])
        muestra.append({
            "codigo": propiedades.get("NTRCODIGO", "Sin código"),
            "nombre": propiedades.get("NTRNOMBRE", "Sin nombre"),
            "direccion": propiedades.get("NTRDIRECCION", "Sin dirección"),
            "longitud": coordenadas[0] if len(coordenadas) > 0 else None,
            "latitud": coordenadas[1] if len(coordenadas) > 1 else None,
        })

    return {
        "localidad": localidad,
        "total_paraderos": total,
        "muestra": muestra,
        "fecha_consulta": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fuente": FUENTE,
    }


def descargar_json(url):
    """Hace la petición HTTP y transforma la respuesta JSON en un diccionario Python."""
    solicitud = Request(url, headers={"User-Agent": "ActividadSENA-Python/1.0"})
    with urlopen(solicitud, timeout=20) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


class ManejadorAPI(BaseHTTPRequestHandler):
    def enviar_json(self, datos, estado=200):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        ruta = urlparse(self.path)
        if ruta.path == "/api/indicadores":
            parametros = parse_qs(ruta.query)
            localidad = parametros.get("localidad", [""])[0]
            if localidad not in LOCALIDADES:
                self.enviar_json({
                    "error": "La localidad no es válida.",
                    "localidades_disponibles": list(LOCALIDADES.keys()),
                }, 400)
                return
            try:
                self.enviar_json(consultar_arcgis(localidad))
            except Exception:
                self.enviar_json({"error": "No fue posible consultar Datos Abiertos Bogotá."}, 502)
            return

        if ruta.path == "/api/localidades":
            self.enviar_json({"localidades": list(LOCALIDADES.keys())})
            return

        if ruta.path == "/":
            self.enviar_pagina()
            return

        self.enviar_json({"error": "Ruta no encontrada."}, 404)

    def enviar_pagina(self):
        opciones = "".join(f"<option>{nombre}</option>" for nombre in LOCALIDADES)
        pagina = f"""<!doctype html><html lang='es'><head><meta charset='utf-8'>
        <meta name='viewport' content='width=device-width,initial-scale=1'>
        <title>Indicadores SITP - API Python</title><style>
        body{{font-family:Arial,sans-serif;background:#f3f7fb;color:#17324a;margin:0}}main{{max-width:820px;margin:45px auto;padding:0 20px}}
        section{{background:#fff;border-radius:14px;padding:28px;box-shadow:0 4px 15px #1234}}h1{{color:#075d83}}select,button{{padding:11px;border-radius:7px;font:inherit}}select{{min-width:210px;border:1px solid #c7d6df}}button{{border:0;background:#087b96;color:white;font-weight:bold;cursor:pointer}}#resultado{{margin-top:22px}}table{{width:100%;border-collapse:collapse;margin-top:15px;font-size:14px}}td,th{{padding:10px;border-bottom:1px solid #dce8ed;text-align:left}}th{{background:#edf7f8}}.nota{{color:#60798c;font-size:13px}}</style></head>
        <body><main><section><h1>Indicadores de movilidad</h1>
        <label>Localidad <select id='localidad'><option value=''>Selecciona una localidad</option>{opciones}</select></label>
        <button onclick='consultar()'>Consultar indicador</button><div id='resultado'></div>
        <p class='nota'>Este módulo muestra ubicación de paraderos; la fuente no publica datos de uso de pasajeros.</p></section></main>
        <script>async function consultar(){{const localidad=document.getElementById('localidad').value;const caja=document.getElementById('resultado');if(!localidad){{caja.textContent='Selecciona una localidad.';return}}caja.textContent='Consultando API Python...';try{{const r=await fetch('/api/indicadores?localidad='+encodeURIComponent(localidad));const d=await r.json();if(!r.ok)throw new Error(d.error);let filas=d.muestra.map(x=>`<tr><td>${{x.codigo}}</td><td>${{x.nombre}}</td><td>${{x.direccion}}</td></tr>`).join('');caja.innerHTML=`<h2>${{d.total_paraderos}} paraderos encontrados en ${{d.localidad}}</h2><p class='nota'>Consulta: ${{d.fecha_consulta}}. A continuación se muestran los primeros 5 registros devueltos por la API.</p><table><tr><th>Código</th><th>Nombre</th><th>Dirección</th></tr>${{filas}}</table>`}}catch(e){{caja.textContent=e.message}}}}</script></body></html>"""
        cuerpo = pagina.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, formato, *argumentos):
        # Se evita llenar la consola con registros en cada consulta del navegador.
        return


if __name__ == "__main__":
    servidor = ThreadingHTTPServer(("127.0.0.1", 5000), ManejadorAPI)
    print("API Python activa en http://127.0.0.1:5000")
    print("Ejemplo de endpoint: http://127.0.0.1:5000/api/indicadores?localidad=Suba")
    servidor.serve_forever()
