<?php
// Actividad SENA: consulta de paraderos SITP con PHP puro y servicio ArcGIS REST.
// Fuente oficial del conjunto de datos: https://datosabiertos.bogota.gov.co/dataset/paraderos-sitp-bogota-d-c
$fuenteDatos = 'https://datosabiertos.bogota.gov.co/dataset/paraderos-sitp-bogota-d-c';

// Localidades disponibles y cajas geográficas aproximadas (longitud, latitud).
$localidades = [
    'Usaquén' => '-74.100,4.680,-74.000,4.840',
    'Chapinero' => '-74.100,4.620,-74.030,4.710',
    'Santa Fe' => '-74.130,4.530,-74.030,4.650',
    'San Cristóbal' => '-74.130,4.500,-74.020,4.620',
    'Usme' => '-74.220,4.420,-74.070,4.580',
    'Tunjuelito' => '-74.170,4.550,-74.100,4.620',
    'Bosa' => '-74.220,4.580,-74.130,4.680',
    'Kennedy' => '-74.200,4.570,-74.090,4.670',
    'Fontibón' => '-74.190,4.620,-74.100,4.710',
    'Engativá' => '-74.160,4.650,-74.080,4.740',
    'Suba' => '-74.150,4.700,-74.020,4.840',
    'Barrios Unidos' => '-74.100,4.650,-74.050,4.690',
    'Teusaquillo' => '-74.100,4.610,-74.050,4.660',
    'Los Mártires' => '-74.110,4.590,-74.060,4.630',
    'Antonio Nariño' => '-74.130,4.560,-74.080,4.610',
    'Puente Aranda' => '-74.150,4.580,-74.080,4.650',
    'La Candelaria' => '-74.090,4.570,-74.050,4.610',
    'Rafael Uribe Uribe' => '-74.140,4.530,-74.070,4.600',
    'Ciudad Bolívar' => '-74.230,4.450,-74.080,4.590',
    'Sumapaz' => '-74.450,3.950,-74.050,4.550'
];

$localidad = trim($_GET['localidad'] ?? '');
$mensaje = '';
$paraderos = [];

// Validación básica: se verifica que el usuario elija una localidad permitida.
if (isset($_GET['consultar'])) {
    if ($localidad === '' || !array_key_exists($localidad, $localidades)) {
        $mensaje = 'Selecciona una localidad válida antes de realizar la consulta.';
    } else {
        // Construcción de la URL ArcGIS REST que devuelve los datos en formato GeoJSON.
        $parametros = http_build_query([
            'where' => '1=1',
            'geometry' => $localidades[$localidad],
            'geometryType' => 'esriGeometryEnvelope',
            'spatialRel' => 'esriSpatialRelIntersects',
            'inSR' => 4326,
            'outFields' => 'NTRCODIGO,NTRNOMBRE,NTRDIRECCION',
            'returnGeometry' => 'true',
            'resultRecordCount' => 100,
            'f' => 'geojson'
        ]);
        $url = 'https://services2.arcgis.com/NEwhEo9GGSHXcRXV/arcgis/rest/services/Paraderos_SITP_Bogot%C3%A1_D_C/FeatureServer/0/query?' . $parametros;

        // Consumo HTTP con file_get_contents y contexto con tiempo máximo de espera.
        $contexto = stream_context_create([
            'http' => ['timeout' => 15, 'header' => "User-Agent: ActividadSENA/1.0\r\n"]
        ]);
        $respuesta = @file_get_contents($url, false, $contexto);

        if ($respuesta === false) {
            $mensaje = 'No fue posible conectar con el servicio de Datos Abiertos Bogotá. Intenta nuevamente.';
        } else {
            // Decodificación JSON: convierte la respuesta de la API en arreglo asociativo PHP.
            $datos = json_decode($respuesta, true);
            if (!is_array($datos) || isset($datos['error'])) {
                $mensaje = 'El servicio respondió con un formato no válido.';
            } elseif (empty($datos['features'])) {
                $mensaje = 'No se encontraron paraderos para la localidad seleccionada.';
            } else {
                // Recorrido de los resultados GeoJSON para presentarlos después en la tabla HTML.
                foreach ($datos['features'] as $feature) {
                    $propiedades = $feature['properties'] ?? [];
                    $coordenadas = $feature['geometry']['coordinates'] ?? [];
                    $paraderos[] = [
                        'codigo' => $propiedades['NTRCODIGO'] ?? 'Sin código',
                        'nombre' => $propiedades['NTRNOMBRE'] ?? 'Sin nombre',
                        'direccion' => $propiedades['NTRDIRECCION'] ?? 'Sin dirección',
                        'longitud' => $coordenadas[0] ?? 'No disponible',
                        'latitud' => $coordenadas[1] ?? 'No disponible'
                    ];
                }
            }
        }
    }
}
?>
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Paraderos SITP Bogotá</title>
    <style>
        *{box-sizing:border-box} body{margin:0;background:#f3f7fb;color:#1d3448;font-family:Arial,sans-serif}
        main{max-width:1100px;margin:45px auto;padding:0 22px}.hero{padding:30px;border-radius:16px;background:linear-gradient(120deg,#075d83,#1194a0);color:#fff}
        h1{margin:0 0 10px;font-size:32px}.hero p{margin:0;color:#d8f2f3}.card{margin-top:22px;padding:25px;border-radius:14px;background:#fff;box-shadow:0 5px 18px #1e4f7014}
        form{display:flex;gap:12px;align-items:end;flex-wrap:wrap}label{display:grid;gap:7px;font-size:13px;font-weight:bold}select,button{height:42px;border-radius:8px;padding:0 12px;font:inherit}select{min-width:220px;border:1px solid #cddde7}button{border:0;background:#087b96;color:#fff;font-weight:bold;cursor:pointer}
        .mensaje{margin-top:20px;padding:13px;border-radius:8px;background:#fff4dd;color:#8a5b00}.resultado{margin-top:25px}.contador,.fuente{color:#667e91;font-size:13px}.fuente a{color:#087188}.modulo-python{display:inline-block;margin-top:14px;padding:10px 13px;border-radius:8px;background:#e7f5f8;color:#07657d;font-size:14px;font-weight:bold;text-decoration:none}table{width:100%;margin-top:12px;border-collapse:collapse;font-size:14px}th,td{padding:12px;text-align:left;border-bottom:1px solid #e6eef4}th{background:#edf7f8;color:#087188}td:nth-child(4),td:nth-child(5){font-family:monospace;color:#60798c}@media(max-width:650px){main{margin-top:20px}table{font-size:12px}th,td{padding:9px}}
    </style>
</head>
<body>
<main>
    <section class="hero"><h1>Consulta de paraderos SITP</h1><p>Datos obtenidos del servicio público de Datos Abiertos Bogotá.</p></section>
    <section class="card">
        <form method="get">
            <label for="localidad">Localidad de Bogotá
                <select name="localidad" id="localidad" required>
                    <option value="">Selecciona una localidad</option>
                    <?php foreach ($localidades as $nombre => $caja): ?>
                        <option value="<?= htmlspecialchars($nombre) ?>" <?= $localidad === $nombre ? 'selected' : '' ?>><?= htmlspecialchars($nombre) ?></option>
                    <?php endforeach; ?>
                </select>
            </label>
            <button type="submit" name="consultar" value="1">Consultar paraderos</button>
        </form>
        <?php if ($mensaje !== ''): ?><p class="mensaje"><?= htmlspecialchars($mensaje) ?></p><?php endif; ?>
        <?php if (!empty($paraderos)): ?>
            <div class="resultado"><strong>Paraderos cercanos a <?= htmlspecialchars($localidad) ?></strong><p class="contador">Se muestran <?= count($paraderos) ?> resultados.</p>
                <table><thead><tr><th>Código</th><th>Nombre</th><th>Dirección</th><th>Latitud</th><th>Longitud</th></tr></thead><tbody>
                <?php foreach ($paraderos as $paradero): ?>
                    <tr><td><?= htmlspecialchars((string)$paradero['codigo']) ?></td><td><?= htmlspecialchars((string)$paradero['nombre']) ?></td><td><?= htmlspecialchars((string)$paradero['direccion']) ?></td><td><?= htmlspecialchars((string)$paradero['latitud']) ?></td><td><?= htmlspecialchars((string)$paradero['longitud']) ?></td></tr>
                <?php endforeach; ?>
                </tbody></table>
            </div>
        <?php endif; ?>
        <a class="modulo-python" href="http://127.0.0.1:5000/" target="_blank" rel="noopener">Abrir módulo API Python: indicadores de movilidad</a>
        <p class="fuente">Fuente: <a href="<?= htmlspecialchars($fuenteDatos) ?>" target="_blank" rel="noopener">Datos Abiertos Bogotá — Paraderos SITP Bogotá D.C.</a></p>
    </section>
</main>
</body>
</html>
