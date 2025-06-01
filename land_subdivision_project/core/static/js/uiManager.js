// Módulo para manejar la interfaz de usuario
const UIManager = (() => {
    const initEventListeners = () => {
        // Botones
        document.getElementById('save-polygon-btn').addEventListener('click', async () => {
            const result = await TerrainManager.savePolygon();
            if (result) {
                updateStatus(true);
            }
        });
        
        document.getElementById('clear-map-btn').addEventListener('click', MapManager.clearMap);
        
        document.getElementById('load-polygon-btn').addEventListener('click', async () => {
            const terrenoId = document.getElementById('load-terreno-id').value.trim();
            const data = await TerrainManager.loadPolygon(terrenoId);
            
            if (data) {
                MapManager.clearMap();
                
                const geojsonLayer = L.geoJSON(JSON.parse(data.geometria_geojson), {
                    style: {
                        color: '#3388ff',
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.3
                    }
                });
                
                MapManager.getDrawnItems().addLayer(geojsonLayer.getLayers()[0]);
                // ✅ Corregido: usar MapManager.getMap()
                MapManager.getMap().fitBounds(geojsonLayer.getBounds());
                
                document.getElementById('geojson-output').value = JSON.stringify(JSON.parse(data.geometria_geojson), null, 2);
                document.getElementById('terreno-name').value = data.nombre_terreno;
                
                TerrainManager.setCurrentTerreno(data.id, data.nombre_terreno);
                updateStatus(true);
                updateLotesInfo();
                
                const area = L.GeometryUtil.geodesicArea(geojsonLayer.getLayers()[0].getLatLngs()[0]);
                geojsonLayer.getLayers()[0].bindTooltip(
                    `${data.nombre_terreno}<br>Área: ${(area).toFixed(2)} m²`, 
                    {permanent: false, direction: 'top'}
                ).openTooltip();
            }
        });
        
        document.getElementById('subdivide-btn').addEventListener('click', SubdivisionManager.subdivideCurrentPolygon);
        document.getElementById('export-lotes-btn').addEventListener('click', SubdivisionManager.exportLotesGeoJSON);
        document.getElementById('save-lotes-btn').addEventListener('click', SubdivisionManager.saveLotesToDatabase);
    };
    
    const updateStatus = (hasTerreno) => {
        const statusElement = document.getElementById('terreno-status');
        const statusTextElement = document.getElementById('terreno-status-text');
        const { id: currentTerrenoId } = TerrainManager.getCurrentTerreno();
        
        if (hasTerreno) {
            statusElement.className = 'status-indicator status-active';
            statusTextElement.textContent = currentTerrenoId ? 'Terreno cargado' : 'Terreno nuevo (no guardado)';
            document.getElementById('current-terreno-id').value = currentTerrenoId || 'Nuevo';
        } else {
            statusElement.className = 'status-indicator status-inactive';
            statusTextElement.textContent = 'No hay terreno cargado';
            document.getElementById('current-terreno-id').value = 'N/A';
        }
    };
    
    const updateLotesInfo = (count = 0) => {
        const lotesInfo = document.getElementById('lotes-resultantes-info');
        const lotesDetails = document.getElementById('lotes-details');
        
        if (count > 0) {
            lotesInfo.innerHTML = `<strong>${count}</strong> lotes generados:`;
        } else {
            lotesInfo.textContent = 'No se han generado lotes aún.';
            lotesDetails.innerHTML = '';
        }
    };
    
    return {
        initEventListeners,
        updateStatus,
        updateLotesInfo
    };
})();
