// Módulo para manejar la lógica de terrenos
const TerrainManager = (() => {
    let currentTerrenoId = null;
    let currentTerrenoName = '';
    let currentTerrenoGeoJSON = null; // GeoJSON actual cargado o guardado
    let csrfToken = '';
    let currentProjectId = 1; // Por defecto, pero ahora se puede establecer dinámicamente

    // Setter para el CSRF Token
    const setCSRFToken = (token) => {
        csrfToken = token;
    };

    // Setter dinámico para el projectId
    const setCurrentProjectId = (projectId) => {
        currentProjectId = projectId;
    };

    // Setter para el terreno actual
    const setCurrentTerreno = (id, name, geojson = null) => {
        currentTerrenoId = id;
        currentTerrenoName = name;
        currentTerrenoGeoJSON = geojson;

        document.getElementById('current-terreno-id').value = id || 'N/A';
        document.getElementById('terreno-name').value = name || '';
    };

    // Guarda el polígono actual en el servidor
const savePolygon = async () => {

    console.log('=== DEBUG SAVEPOLYGON ===');
    console.log('currentProjectId:', currentProjectId);
    console.log('currentTerrenoName:', currentTerrenoName);
    console.log('csrfToken:', csrfToken ? 'Token presente' : 'Token faltante');
    const geojsonDataRaw = document.getElementById('geojson-output').value;

    if (!geojsonDataRaw) {
        Swal.fire({
            icon: 'warning',
            title: 'Polígono faltante',
            text: 'Por favor, dibuje un polígono primero.'
        });
        return null;
    }

    currentTerrenoName = document.getElementById('terreno-name').value.trim();
    if (!currentTerrenoName) {
        Swal.fire({
            icon: 'warning',
            title: 'Nombre requerido',
            text: 'Por favor, ingrese un nombre para el terreno.'
        });
        return null;
    }

    // Validar que el GeoJSON es JSON válido y extraer la geometría
    let geojsonData;
    try {
        geojsonData = JSON.parse(geojsonDataRaw);
        
        // Verificar que tiene la estructura de Feature
        if (!geojsonData.geometry || !geojsonData.geometry.type || !geojsonData.geometry.coordinates) {
            throw new Error('El GeoJSON no tiene la estructura correcta (geometry.type y geometry.coordinates son requeridos)');
        }
    } catch (e) {
        Swal.fire({
            icon: 'error',
            title: 'GeoJSON inválido',
            text: e.message || 'La geometría del polígono no es un JSON válido.'
        });
        return null;
    }

    try {
        const response = await fetch('/core/api/terrenos/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                proyecto_id: currentProjectId, 
                nombre_terreno: currentTerrenoName,
                geometria_geojson: JSON.stringify(geojsonData.geometry) // Solo enviar la geometría como string
            })
        });

        if (response.ok) {
            const data = await response.json();
            currentTerrenoId = data.id;
            currentTerrenoGeoJSON = geojsonDataRaw; // Guardar en memoria
            Swal.fire({
                icon: 'success',
                title: 'Guardado exitoso',
                text: `Terreno guardado con ID: ${data.id}`,
                timer: 2000
            });
            return data;
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || JSON.stringify(errorData));
        }
    } catch (error) {
        console.error('Error al guardar polígono:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error al guardar',
            text: error.message || 'Error de red o servidor al guardar el polígono.'
        });
        return null;
    }
};

    // Carga el polígono de un terreno desde la API
    const loadPolygon = async (terrenoId) => {
        if (!terrenoId) {
            Swal.fire({
                icon: 'warning',
                title: 'ID faltante',
                text: 'Por favor, ingrese un ID de terreno.'
            });
            return null;
        }

        try {
            const response = await fetch(`/core/api/terrenos/${terrenoId}/`);
            if (response.ok) {
                const data = await response.json();
                currentTerrenoGeoJSON = data.geometria_geojson; // Guardar en memoria
                return data;
            } else if (response.status === 404) {
                throw new Error('Terreno no encontrado. Verifique el ID.');
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || JSON.stringify(errorData));
            }
        } catch (error) {
            console.error('Error al cargar polígono:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error al cargar',
                text: error.message || 'Error de red o servidor al cargar el polígono.'
            });
            return null;
        }
    };

    // Envía la solicitud para subdividir el polígono
    const subdivideTerreno = async (terrenoId, geojsonPolygonStr, numLots, method) => {
        if (!terrenoId) {
            Swal.fire({ icon: 'warning', title: 'Terreno faltante', text: 'Por favor, guarde o cargue un terreno primero.' });
            return null;
        }

        if (!numLots || numLots <= 0) {
            Swal.fire({ icon: 'warning', title: 'Número inválido', text: 'Por favor, ingrese un número válido de lotes (mayor que 0).' });
            return null;
        }

        if (!geojsonPolygonStr) {
            Swal.fire({ icon: 'warning', title: 'Geometría faltante', text: 'No se pudo obtener la geometría del polígono para subdividir.' });
            return null;
        }

        try {
            const url = `/core/api/terrenos/${terrenoId}/subdivide/`;
            console.log("URL de subdivisión:", url);

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    geojson_polygon_str: geojsonPolygonStr,
                    num_lots: numLots,
                    method: method
                })
            });

            if (response.ok) {
                return await response.json();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || errorData.detail || JSON.stringify(errorData));
            }
        } catch (error) {
            console.error('Error en subdivideTerreno (llamada API):', error);
            throw error; // Dejar que el llamador lo maneje
        }
    };

    // API del módulo
    return {
        setCSRFToken,
        setCurrentProjectId, // Nueva función
        setCurrentTerreno,
        savePolygon,
        loadPolygon,
        subdivideTerreno,
        getCurrentTerrenoGeoJSON: () => currentTerrenoGeoJSON,
        getCurrentTerreno: () => ({
            id: currentTerrenoId,
            name: currentTerrenoName,
            geojson: currentTerrenoGeoJSON
        })
    };
})();
