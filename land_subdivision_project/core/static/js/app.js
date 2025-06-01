// static/js/app.js (o tu archivo de inicialización principal)

document.addEventListener('DOMContentLoaded', () => {
    // 1. Obtener el CSRF Token (si aún no lo tienes globalmente)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');
    TerrainManager.setCSRFToken(csrftoken);

    // 2. Obtener el PROYECTO_ID inyectado desde Django y pasárselo a TerrainManager
    // Asegúrate de que el script en map_interface.html ya haya definido PROYECTO_ID
    if (typeof PROYECTO_ID !== 'undefined' && PROYECTO_ID !== null) {
        TerrainManager.setProjectId(PROYECTO_ID);
    } else {
        console.error("PROYECTO_ID no está definido en el contexto global. El guardado podría fallar.");
        Swal.fire('Error de Configuración', 'No se pudo cargar el ID del proyecto. Recargue la página.', 'error');
    }

    // 3. Inicializar el mapa y los eventos
    MapManager.initMap();
    MapManager.setupDrawControl();

    // 4. Configurar listeners de la UI
    // Evento para el botón "Guardar Terreno"
    document.getElementById('save-polygon-btn').addEventListener('click', async () => {
        // La lógica de guardado está ahora encapsulada en TerrainManager.savePolygon()
        const savedData = await TerrainManager.savePolygon();
        if (savedData) {
            // Si el terreno se guardó exitosamente, actualiza la UI
            MapManager.updateTerrenoStatus(true);
            document.getElementById('current-terreno-id').value = savedData.id;
            // Opcional: Cargar el terreno recién guardado en el mapa
            // MapManager.loadGeoJSON(JSON.parse(savedData.geometria_geojson));
        }
    });

    // Evento para el botón "Limpiar Mapa"
    document.getElementById('clear-map-btn').addEventListener('click', () => {
        MapManager.clearMap();
        MapManager.updateTerrenoStatus(false);
        document.getElementById('current-terreno-id').value = 'N/A';
        document.getElementById('terreno-name').value = '';
        document.getElementById('geojson-output').value = '';
    });

    // Evento para el botón "Buscar Terreno"
    document.getElementById('load-polygon-btn').addEventListener('click', async () => {
        const terrenoId = document.getElementById('load-terreno-id').value;
        const loadedData = await TerrainManager.loadPolygon(terrenoId);
        if (loadedData) {
            MapManager.clearMap();
            MapManager.loadGeoJSON(JSON.parse(loadedData.geometria_geojson)); // Parsear a objeto JS
            TerrainManager.setCurrentTerreno(loadedData.id, loadedData.nombre_terreno, loadedData.geometria_geojson); // Actualiza también el GeoJSON
            MapManager.updateTerrenoStatus(true);
        }
    });

    // Evento para el botón "Subdividir Terreno"
    document.getElementById('subdivide-btn').addEventListener('click', async () => {
        const terrenoId = TerrainManager.getCurrentTerreno().id;
        const geojsonPolygonStr = TerrainManager.getCurrentTerrenoGeoJSON(); // Obtener el GeoJSON guardado
        const numLots = document.getElementById('num-lots').value;
        const method = document.getElementById('subdivision-method').value;

        try {
            const subdivisionResult = await TerrainManager.subdivideTerreno(terrenoId, geojsonPolygonStr, numLots, method);
            if (subdivisionResult) {
                console.log('Resultado de subdivisión:', subdivisionResult);
                // Aquí deberías pasar subdivisionResult a MapManager para dibujar los lotes
                MapManager.displaySubdivisionResults(subdivisionResult.lotes_creados);
                // Actualizar la interfaz de usuario con los detalles de los lotes
                UIManager.updateLotesDetails(subdivisionResult.lotes_creados);
                Swal.fire('¡Subdivisión Exitosa!', 'Los lotes han sido generados y dibujados en el mapa.', 'success');
            }
        } catch (error) {
            console.error('Error al subdividir desde UI:', error);
            Swal.fire('Error de Subdivisión', error.message || 'Ocurrió un error al intentar subdividir el terreno.', 'error');
        }
    });
});