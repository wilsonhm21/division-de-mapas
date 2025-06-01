// Módulo para manejar la subdivisión de terrenos
const SubdivisionManager = (() => {
    const subdivideCurrentPolygon = async () => {
        const currentTerreno = TerrainManager.getCurrentTerreno();
        const currentTerrenoId = currentTerreno ? currentTerreno.id : null;

        // --- Obtener la geometría del polígono actual desde MapManager ---
        let geojsonToSubdivide = null;
        const drawnLayer = MapManager.getCurrentPolygonLayer(); // Obtener la capa dibujada
        if (drawnLayer) {
            // Convertir la capa de Leaflet a GeoJSON y luego a string JSON de la geometría
            geojsonToSubdivide = JSON.stringify(drawnLayer.toGeoJSON().geometry); 
        }
        // --- Fin de la obtención de geometría ---

        if (!currentTerrenoId || !geojsonToSubdivide) {
            Swal.fire({
                icon: 'warning',
                title: 'Terreno o geometría faltante',
                text: 'Por favor, dibuje un polígono y asegúrese de que esté en el mapa.'
            });
            return;
        }
        
        const numLots = parseInt(document.getElementById('num-lots').value);
        if (isNaN(numLots) || numLots <= 0) {
            Swal.fire({
                icon: 'warning',
                title: 'Número inválido',
                text: 'Por favor, ingrese un número válido de lotes (mayor que 0).'
            });
            return;
        }
        
        const method = document.getElementById('subdivision-method').value;
        
        const loadingAlert = Swal.fire({
            title: `Procesando subdivisión (${method})`,
            html: 'Por favor espere...',
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });
        
        try {
            // Pasar el GeoJSON a subdivideTerreno
            const data = await TerrainManager.subdivideTerreno(currentTerrenoId, geojsonToSubdivide, numLots, method);
            
            if (data.features && data.features.length > 0) {
                MapManager.addResultLots(data); 
                
                let totalArea = 0;
                const lotesDetails = document.getElementById('lotes-details');
                lotesDetails.innerHTML = '';
                
                data.features.forEach((feature, index) => {
                    const area = feature.properties.area_sqm; 
                    if (area) {
                        totalArea += area;
                    }

                    // Generar el color de forma consistente para la UI y el mapa
                    const color = `hsl(${index * 360 / data.features.length}, 70%, 50%)`;
                    
                    const lotInfo = document.createElement('div');
                    lotInfo.className = 'lot-info';
                    lotInfo.innerHTML = `
                        <strong>Lote ${index + 1}</strong>
                        <button class="btn btn-sm btn-outline-secondary float-end" 
                                onclick="MapManager.zoomToLot(${index})"
                                title="Centrar en este lote">
                            <i class="bi bi-zoom-in"></i>
                        </button>
                        <br>Área: ${(area || 0).toFixed(2)} m²
                        <br>Porcentaje: ${((area / totalArea) * 100).toFixed(1) || 0}%
                        <br><small style="color: ${color}">■</small> Color identificador
                    `;
                    lotesDetails.appendChild(lotInfo);
                });
                
                const avgArea = totalArea / data.features.length;
                
                UIManager.updateLotesInfo(data.features.length, totalArea, method); // Pasar totalArea y method
                document.getElementById('lotes-resultantes-info').innerHTML = `
                    <strong>${data.features.length}</strong> lotes generados por <strong>${method}</strong>:
                    <br>Área total: ${totalArea.toFixed(2)} m²
                    <br>Área promedio: ${avgArea.toFixed(2)} m² por lote
                `;
                
                loadingAlert.close();
                Swal.fire({
                    icon: 'success',
                    title: 'Subdivisión completada',
                    html: `
                        <div>Método: <strong>${method}</strong></div>
                        <div>Lotes creados: <strong>${data.features.length}</strong></div>
                        <div>Área total: <strong>${totalArea.toFixed(2)} m²</strong></div>
                    `,
                    timer: 3000
                });
            } else {
                throw new Error(data.error || 'No se generaron lotes válidos.');
            }
        } catch (error) {
            console.error('Error en subdivideCurrentPolygon:', error);
            loadingAlert.close();
            
            Swal.fire({
                icon: 'error',
                title: 'Error en subdivisión',
                html: `
                    <div>Método: <strong>${method}</strong></div>
                    <div>Error: <strong>${error.message || 'Error desconocido'}</strong></div>
                `,
                footer: 'Revise la consola para más detalles'
            });
            
            document.getElementById('lotes-resultantes-info').textContent = 
                `Error en ${method}: ${error.message || 'Error en el proceso'}`;
        }
    };
    
    const exportLotesGeoJSON = () => {
        const resultLots = MapManager.getResultLots(); // Obtener los lotes resultantes del mapa
        if (!resultLots || resultLots.features.length === 0) { // Acceder a .features
            Swal.fire({
                icon: 'warning',
                title: 'No hay lotes',
                text: 'No hay lotes para exportar. Realice una subdivisión primero.'
            });
            return;
        }
        
        const currentTerreno = TerrainManager.getCurrentTerreno();
        const filename = `lotes_subdivididos_${currentTerreno.id || 'nuevo'}.geojson`;
        const dataStr = JSON.stringify(resultLots, null, 2); // Stringify el FeatureCollection completo
        const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);

        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', filename);
        linkElement.click();
    };
    
    const saveLotesToDatabase = async () => {
        const resultLots = MapManager.getResultLots();
        if (!resultLots || resultLots.features.length === 0) {
            Swal.fire({
                icon: 'warning',
                title: 'No hay lotes',
                text: 'No hay lotes para guardar. Realice una subdivisión primero.'
            });
            return;
        }
        
        // Aquí debes implementar la lógica para enviar cada lote a tu API de LoteResultante
        // o un endpoint que acepte una FeatureCollection de lotes.
        // Esto es un placeholder.
        console.log('Guardando lotes:', resultLots);
        Swal.fire({
            icon: 'info',
            title: 'Guardar Lotes',
            text: 'Esta funcionalidad se implementará próximamente.'
        });
    };
    
    return {
        subdivideCurrentPolygon,
        exportLotesGeoJSON,
        saveLotesToDatabase
    };
})();