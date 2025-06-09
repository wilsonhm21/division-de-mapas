document.addEventListener('DOMContentLoaded', () => {
    // Función para obtener cookie CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            document.cookie.split(';').forEach(cookie => {
                const c = cookie.trim();
                if (c.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(c.substring(name.length + 1));
                }
            });
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');
    TerrainManager.setCSRFToken(csrftoken);

    if (typeof PROYECTO_ID !== 'undefined' && PROYECTO_ID !== null) {
        // CORRECCIÓN CLAVE: Usar el nombre de función correcto
        TerrainManager.setCurrentProjectId(PROYECTO_ID);
    } else {
        Swal.fire('Error de Configuración', 'No se pudo cargar el ID del proyecto. Recargue la página.', 'error');
        // Puedes deshabilitar botones aquí si quieres
        return;
    }

    // Inicialización del mapa. Esto ya incluye el control de dibujo.
    MapManager.initMap();

    // Event Listener para el botón Guardar Terreno
    const saveBtn = document.getElementById('save-polygon-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            try {
                const savedData = await TerrainManager.savePolygon();
                if (savedData) {
                    // Usar UIManager para actualizar el estado
                    UIManager.updateStatus(true);
                    document.getElementById('current-terreno-id').value = savedData.id;
                }
            } catch (error) {
                Swal.fire('Error al guardar', error.message || 'No se pudo guardar el terreno.', 'error');
            }
        });
    }

    // Event Listener para el botón Limpiar Mapa
    const clearBtn = document.getElementById('clear-map-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            MapManager.clearMap();
            // Usar UIManager para actualizar el estado
            UIManager.updateStatus(false);
            document.getElementById('current-terreno-id').value = 'N/A';
            document.getElementById('terreno-name').value = '';
            document.getElementById('geojson-output').value = '';
        });
    }

    // Event Listener para el botón Cargar Terreno Existente
    const loadBtn = document.getElementById('load-polygon-btn');
    if (loadBtn) {
        loadBtn.addEventListener('click', async () => {
            const terrenoId = document.getElementById('load-terreno-id').value.trim();
            if (!terrenoId) {
                return Swal.fire('Error', 'Ingrese un ID de terreno válido para cargar.', 'warning');
            }
            try {
                const loadedData = await TerrainManager.loadPolygon(terrenoId);
                if (loadedData) {
                    MapManager.clearMap();
                    // Asegúrate de que MapManager.loadGeoJSON exista en MapManager.js
                    // y que maneje la adición del GeoJSON al mapa.
                    MapManager.loadGeoJSON(JSON.parse(loadedData.geometria_geojson));
                    TerrainManager.setCurrentTerreno(loadedData.id, loadedData.nombre_terreno, loadedData.geometria_geojson);
                    UIManager.updateStatus(true);
                } else {
                    Swal.fire('No encontrado', 'No se encontró el terreno con ese ID.', 'info');
                }
            } catch (error) {
                Swal.fire('Error al cargar', error.message || 'No se pudo cargar el terreno.', 'error');
            }
        });
    }

    // Event Listener para el botón Subdividir Terreno
    const subdivideBtn = document.getElementById('subdivide-btn');
    if (subdivideBtn) {
        subdivideBtn.addEventListener('click', async () => {
            const currentTerreno = TerrainManager.getCurrentTerreno();
            if (!currentTerreno || !currentTerreno.id) {
                return Swal.fire('Error', 'No hay un terreno seleccionado para subdividir.', 'warning');
            }

            const numLotsInput = document.getElementById('num-lots');
            const methodSelect = document.getElementById('subdivision-method');

            if (!numLotsInput || !methodSelect) {
                return Swal.fire('Error', 'Faltan elementos en el formulario.', 'error');
            }

            const numLots = parseInt(numLotsInput.value);
            if (isNaN(numLots) || numLots <= 0) {
                return Swal.fire('Error', 'Ingrese un número válido de lotes mayor a 0.', 'warning');
            }
            const method = methodSelect.value;

            try {
                const subdivisionResult = await TerrainManager.subdivideTerreno(currentTerreno.id, currentTerreno.geojson, numLots, method);
                if (subdivisionResult) {
                    // Asegúrate de que MapManager.displaySubdivisionResults exista en MapManager.js
                    MapManager.displaySubdivisionResults(subdivisionResult.lotes_creados);
                    // Asegúrate de que UIManager.updateLotesDetails exista en UIManager.js
                    UIManager.updateLotesDetails(subdivisionResult.lotes_creados);
                    Swal.fire('¡Subdivisión Exitosa!', 'Los lotes han sido generados y dibujados en el mapa.', 'success');
                }
            } catch (error) {
                Swal.fire('Error de Subdivisión', error.message || 'Ocurrió un error al intentar subdividir el terreno.', 'error');
            }
        });
    }
});