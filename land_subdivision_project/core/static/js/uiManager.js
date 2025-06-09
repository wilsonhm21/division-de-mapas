const UIManager = (() => {
    const initEventListeners = () => {
        document.getElementById('save-polygon-btn')?.addEventListener('click', async () => {
            try {
                const result = await TerrainManager.savePolygon();
                if (result) updateStatus(true);
            } catch (error) {
                console.error('Error guardando polígono:', error);
                alert('No se pudo guardar el polígono. Revisa la consola para más detalles.');
            }
        });
        
        document.getElementById('clear-map-btn')?.addEventListener('click', () => {
            try {
                MapManager.clearMap();
                updateStatus(false);
                updateLotesInfo(0);
            } catch (error) {
                console.error('Error limpiando mapa:', error);
            }
        });
        
        document.getElementById('load-polygon-btn')?.addEventListener('click', async () => {
            try {
                const terrenoId = document.getElementById('load-terreno-id').value.trim();
                if (!terrenoId) {
                    alert('Por favor ingresa un ID válido para cargar el terreno.');
                    return;
                }
                
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
                    MapManager.getMap().fitBounds(geojsonLayer.getBounds());
                    
                    document.getElementById('geojson-output').value = JSON.stringify(JSON.parse(data.geometria_geojson), null, 2);
                    document.getElementById('terreno-name').value = data.nombre_terreno;
                    
                    TerrainManager.setCurrentTerreno(data.id, data.nombre_terreno);
                    updateStatus(true);
                    updateLotesInfo(0);
                    
                    const area = L.GeometryUtil.geodesicArea(geojsonLayer.getLayers()[0].getLatLngs()[0]);
                    geojsonLayer.getLayers()[0].bindTooltip(
                        `${data.nombre_terreno}<br>Área: ${(area).toFixed(2)} m²`, 
                        { permanent: false, direction: 'top' }
                    ).openTooltip();
                } else {
                    alert('No se encontró el terreno con ese ID.');
                    updateStatus(false);
                    updateLotesInfo(0);
                }
            } catch (error) {
                console.error('Error cargando terreno:', error);
                alert('No se pudo cargar el terreno. Revisa la consola para más detalles.');
            }
        });
        
        document.getElementById('subdivide-btn')?.addEventListener('click', async () => {
            try {
                await SubdivisionManager.subdivideCurrentPolygon();
                // Supongamos que subdividir genera lotes, actualiza el contador
                const lotesGeojson = MapManager.getResultLots();
                const count = lotesGeojson?.features?.length || 0;
                updateLotesInfo(count);
            } catch (error) {
                console.error('Error subdividiendo polígono:', error);
                alert('No se pudo subdividir el polígono.');
            }
        });
        
        document.getElementById('export-lotes-btn')?.addEventListener('click', () => {
            try {
                SubdivisionManager.exportLotesGeoJSON();
            } catch (error) {
                console.error('Error exportando lotes:', error);
                alert('No se pudo exportar los lotes.');
            }
        });
        
        document.getElementById('save-lotes-btn')?.addEventListener('click', async () => {
            try {
                await SubdivisionManager.saveLotesToDatabase();
                alert('Lotes guardados exitosamente.');
            } catch (error) {
                console.error('Error guardando lotes:', error);
                alert('No se pudo guardar los lotes.');
            }
        });
    };
    
    const updateStatus = (hasTerreno) => {
        const statusElement = document.getElementById('terreno-status');
        const statusTextElement = document.getElementById('terreno-status-text');
        const currentTerreno = TerrainManager.getCurrentTerreno();
        const currentTerrenoId = currentTerreno?.id || null;
        
        if (statusElement && statusTextElement) {
            if (hasTerreno) {
                statusElement.className = 'status-indicator status-active';
                statusTextElement.textContent = currentTerrenoId ? 'Terreno cargado' : 'Terreno nuevo (no guardado)';
                document.getElementById('current-terreno-id').value = currentTerrenoId || 'Nuevo';
            } else {
                statusElement.className = 'status-indicator status-inactive';
                statusTextElement.textContent = 'No hay terreno cargado';
                document.getElementById('current-terreno-id').value = 'N/A';
            }
        }
    };
    
    const updateLotesInfo = (count = 0) => {
        const lotesInfo = document.getElementById('lotes-resultantes-info');
        const lotesDetails = document.getElementById('lotes-details');
        
        if (lotesInfo && lotesDetails) {
            if (count > 0) {
                lotesInfo.innerHTML = `<strong>${count}</strong> lotes generados:`;
                // Aquí podrías agregar detalles sobre los lotes si quieres
                lotesDetails.innerHTML = ''; // Limpia o agrega info adicional
            } else {
                lotesInfo.textContent = 'No se han generado lotes aún.';
                lotesDetails.innerHTML = '';
            }
        }
    };
    
    return {
        initEventListeners,
        updateStatus,
        updateLotesInfo
    };
})();

// Asegúrate de llamar initEventListeners una vez cargado el DOM:
document.addEventListener('DOMContentLoaded', () => {
    UIManager.initEventListeners();
});
