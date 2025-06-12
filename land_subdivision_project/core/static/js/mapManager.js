// Módulo para manejar el mapa y sus capas
const MapManager = (() => {
    let map;
    let drawnItems;
    let resultLotsLayer;
    let drawControl;
    
    // Variable para almacenar la capa de polígono actualmente dibujada/cargada
    let currentPolygonLayer = null;

    const initMap = () => {
        map = L.map('map').setView([-15.49, -70.13], 13);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);
        
        drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);
        
        resultLotsLayer = new L.FeatureGroup();
        map.addLayer(resultLotsLayer);
        
        // Permitir edición después de crear polígonos
        drawControl = new L.Control.Draw({
            edit: { 
                featureGroup: drawnItems,
                edit: true // ¡Ahora se permite editar!
            },
            draw: {
                polygon: {
                    allowIntersection: false,
                    showArea: true,
                    metric: true,
                    shapeOptions: {
                        color: '#3388ff',
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.3
                    }
                },
                polyline: false, rectangle: false, circle: false, marker: false, circlemarker: false
            }
        });
        map.addControl(drawControl);
        
        map.on(L.Draw.Event.CREATED, handleDrawCreated);
        map.on(L.Draw.Event.EDITED, handleDrawEdited);
        
        // Inicializar el estado en TerrainManager y UI Manager
        if (typeof TerrainManager !== 'undefined' && typeof UIManager !== 'undefined') {
            TerrainManager.setCurrentTerreno(null, '', null);
            UIManager.updateStatus(false);
        } else {
            console.warn("TerrainManager o UIManager no definidos al inicializar MapManager.");
        }
    };
    
    const handleDrawCreated = (e) => {
        const layer = e.layer;
        drawnItems.clearLayers();
        resultLotsLayer.clearLayers();
        drawnItems.addLayer(layer);
        
        currentPolygonLayer = layer;
        const geojsonString = JSON.stringify(layer.toGeoJSON().geometry);
        
        const geojsonOutput = document.getElementById('geojson-output');
        if (geojsonOutput) {
            geojsonOutput.value = JSON.stringify(layer.toGeoJSON(), null, 2);
        }
        
        if (typeof TerrainManager !== 'undefined') {
            TerrainManager.setCurrentTerreno(null, '', geojsonString);
        }
        
        const area = L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]);
        layer.bindTooltip(`Área: ${(area).toFixed(2)} m²`, { permanent: false, direction: 'top' }).openTooltip();
        
        if (typeof UIManager !== 'undefined') {
            UIManager.updateStatus(true);
            UIManager.updateLotesInfo();
        }
    };
    
    const handleDrawEdited = (e) => {
        const layers = e.layers;
        layers.eachLayer((layer) => {
            currentPolygonLayer = layer;
            const geojsonString = JSON.stringify(layer.toGeoJSON().geometry);
            
            const geojsonOutput = document.getElementById('geojson-output');
            if (geojsonOutput) {
                geojsonOutput.value = JSON.stringify(layer.toGeoJSON(), null, 2);
            }
            
            if (typeof TerrainManager !== 'undefined') {
                const { id: currentId, name: currentName } = TerrainManager.getCurrentTerreno();
                TerrainManager.setCurrentTerreno(currentId, currentName, geojsonString);
            }
        });
        resultLotsLayer.clearLayers();
        
        if (typeof UIManager !== 'undefined') {
            UIManager.updateLotesInfo();
        }
    };
    
    const clearMap = () => {
        drawnItems.clearLayers();
        resultLotsLayer.clearLayers();
        
        const geojsonOutput = document.getElementById('geojson-output');
        if (geojsonOutput) geojsonOutput.value = '';
        
        const terrenoName = document.getElementById('terreno-name');
        if (terrenoName) terrenoName.value = '';
        
        currentPolygonLayer = null;
        
        if (typeof TerrainManager !== 'undefined' && typeof UIManager !== 'undefined') {
            TerrainManager.setCurrentTerreno(null, '', null);
            UIManager.updateStatus(false);
            UIManager.updateLotesInfo();
        }
    };
    
    const zoomToLot = (index) => {
        const targetLayer = resultLotsLayer.getLayers()[index];
        if (targetLayer) {
            map.fitBounds(targetLayer.getBounds(), { padding: [50, 50] });
            targetLayer.fire('click');
        }
    };
    
    const addResultLots = (geojsonData) => {
        if (!geojsonData || !geojsonData.features) return;
        
        resultLotsLayer.clearLayers();
        
        geojsonData.features.forEach((feature, index) => {
            const color = `hsl(${Math.random() * 360}, 70%, 50%)`;
            
            const lotLayer = L.geoJSON(feature, {
                style: {
                    color: color,
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.3
                }
            }).addTo(resultLotsLayer);
            
            const area = L.GeometryUtil.geodesicArea(lotLayer.getLayers()[0].getLatLngs()[0]);
            
            lotLayer.getLayers()[0].bindTooltip(
                `Lote ${index + 1}<br>Área: ${(area).toFixed(2)} m²`, 
                { permanent: false, direction: 'top' }
            ).openTooltip();
        });
        
        map.fitBounds(resultLotsLayer.getBounds());
    };
    
    const getResultLots = () => {
        return resultLotsLayer.toGeoJSON();
    };

    const loadGeoJSON = (geojson) => {
    const layer = L.geoJSON(geojson).getLayers()[0];
    if (layer) {
        drawnItems.clearLayers();
        resultLotsLayer.clearLayers();
        drawnItems.addLayer(layer);

        currentPolygonLayer = layer;

        const area = L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]);
        layer.bindTooltip(`Área: ${(area).toFixed(2)} m²`, { permanent: false, direction: 'top' }).openTooltip();

        const geojsonOutput = document.getElementById('geojson-output');
        if (geojsonOutput) {
            geojsonOutput.value = JSON.stringify(layer.toGeoJSON(), null, 2); // ✅ Aquí el cambio
        }

        if (typeof TerrainManager !== 'undefined') {
            TerrainManager.setCurrentTerreno(null, '', JSON.stringify(layer.toGeoJSON().geometry));
        }

        if (typeof UIManager !== 'undefined') {
            UIManager.updateStatus(true);
            UIManager.updateLotesInfo();
        }
    }
};


    
    return {
        initMap,
        clearMap,
        zoomToLot,
        addResultLots,
        getDrawnItems: () => drawnItems,
        getMap: () => map,
        getResultLotsLayer: () => resultLotsLayer,
        getCurrentPolygonLayer: () => currentPolygonLayer,
        getResultLots,
        loadGeoJSON 
    };
})();
        