// Módulo para manejar la lógica de terrenos
const TerrainManager = (() => {
    let currentTerrenoId = null;
    let currentTerrenoName = '';
    let csrfToken = '';
    let currentProyectoId = null; // <--- NUEVA VARIABLE PARA ALMACENAR EL ID DEL PROYECTO
    
    // Variable para almacenar el GeoJSON del polígono actual (después de ser cargado o guardado)
    let currentTerrenoGeoJSON = null; 
    
    const setCSRFToken = (token) => {
        csrfToken = token;
    };

    // Función para establecer el ID del proyecto, llamada desde app.js o directamente si es global
    const setProjectId = (id) => {
        currentProyectoId = id;
        console.log("TerrainManager: Project ID set to", currentProyectoId);
    };
    
    const setCurrentTerreno = (id, name, geojson = null) => { // Añadir parámetro geojson
        currentTerrenoId = id;
        currentTerrenoName = name;
        currentTerrenoGeoJSON = geojson; // Almacenar el GeoJSON cuando se establece el terreno
        document.getElementById('current-terreno-id').value = id || 'N/A';
        document.getElementById('terreno-name').value = name || '';
    };
    
    const savePolygon = async () => {
        const geojsonDataRaw = document.getElementById('geojson-output').value; // Esto ya es un string JSON
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
        
        // **CORRECCIÓN AQUÍ:** Usar currentProyectoId que se establece dinámicamente
        if (currentProyectoId === null || typeof currentProyectoId === 'undefined') {
            Swal.fire({
                icon: 'error',
                title: 'Error de Proyecto',
                text: 'No se pudo obtener el ID del proyecto. Por favor, recargue la página o contacte al soporte.'
            });
            console.error("Error: currentProyectoId no está disponible en TerrainManager.");
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
                    // **CORRECCIÓN AQUÍ:** Cambiar 'proyecto_id' a 'proyecto'
                    proyecto: currentProyectoId, // <--- USA LA VARIABLE DINÁMICA
                    nombre_terreno: currentTerrenoName,
                    geometria_geojson: geojsonDataRaw // Ya es un string, no necesita JSON.stringify de nuevo
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                currentTerrenoId = data.id;
                currentTerrenoGeoJSON = geojsonDataRaw; 
                
                Swal.fire({
                    icon: 'success',
                    title: 'Guardado exitoso',
                    text: `Terreno guardado con ID: ${data.id}`,
                    timer: 2000
                });
                
                return data;
            } else {
                const errorData = await response.json();
                // Mejor manejo de errores del backend
                const errorMessage = errorData.proyecto || errorData.detail || JSON.stringify(errorData);
                throw new Error(errorMessage);
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
    
    const loadPolygon = async (terrenoId) => {
        // ... (Tu función loadPolygon, no necesita cambios aquí) ...
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
                currentTerrenoGeoJSON = data.geometria_geojson; 
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
    
    const subdivideTerreno = async (terrenoId, geojsonPolygonStr, numLots, method) => {
        // ... (Tu función subdivideTerreno, no necesita cambios aquí por ahora) ...
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
            console.log("Datos a enviar para subdivisión:", {
                geojson_polygon_str: geojsonPolygonStr,
                num_lots: numLots,
                method: method
            });

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
                console.error("Error en la respuesta del servidor:", errorData);
                throw new Error(errorData.error || errorData.detail || JSON.stringify(errorData));
            }
        } catch (error) {
            console.error('Error en subdivideTerreno (llamada API):', error);
            throw error;
        }
    };
    
    return {
        setCSRFToken,
        setProjectId, // <--- EXPORTAR LA NUEVA FUNCIÓN
        setCurrentTerreno,
        savePolygon,
        loadPolygon,
        subdivideTerreno,
        getCurrentTerrenoGeoJSON: () => currentTerrenoGeoJSON,
        getCurrentTerreno: () => ({ id: currentTerrenoId, name: currentTerrenoName, geojson: currentTerrenoGeoJSON })
    };
})();