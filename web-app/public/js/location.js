// 
let map;
let polyline;
let decorator;
let currentMarker;
let currentPathData = [];

document.addEventListener("DOMContentLoaded", () => {
   
    if (typeof routePath !== "undefined" && routePath !== null && routePath.length > 0) {
        currentPathData = routePath;
        initMap(currentPathData);
    }
   else {
    map = L.map("map").setView([37.9838, 23.7275], 7);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap",
  }).addTo(map)
 }
    
    setupLiveTracking();


    document.querySelectorAll('input[name="timeRange"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            updatePath(e.target.value);
        });
    });
});


function initMap(path) {
    const lastPoint = [path[path.length - 1].lat, path[path.length - 1].lng];
    map = L.map("map").setView(lastPoint, 16);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "© OpenStreetMap",
    }).addTo(map);

    drawRoute(path);

    
    setTimeout(() => {
        map.flyTo(lastPoint, 17, { animate: true, duration: 1.5 });
    }, 1000);
}

function setupLiveTracking() {
    if (window.mqttWorker) {
        window.mqttWorker.port.addEventListener('message', (e) => {
            const { type, topic, payload } = e.data;

            if (type === 'MQTT_MESSAGE' && topic.endsWith('uplink/gps')) {
                try {
                    const notification = JSON.parse(payload);
                    const entity = notification.data[0];

                    const locationValue = entity.location.value.coordinates;

                   
                    const [lng, lat] = locationValue;

                    const newPoint = {lat,lng, time: new Date().toISOString() };
                    const lastPoint = currentPathData[currentPathData.length - 1];
                    if (!lastPoint || newPoint.time !== lastPoint.time) {
                        console.log("Live Location Received:", newPoint);
                        currentPathData.push(newPoint);

                        
                        drawRoute(currentPathData);

                        map.panTo([newPoint.lat, newPoint.lng]);
                    }
                } catch (err) {
                    console.error("MQTT Payload Error:", err);
                }
            }
        });

        
        window.mqttWorker.port.start();
    }
}


function drawRoute(pathData) {
    if (!map) return;

   
    if (polyline) map.removeLayer(polyline);
    if (decorator) map.removeLayer(decorator);
    if (currentMarker) map.removeLayer(currentMarker);

    if (!pathData || pathData.length === 0) return;

    const latLngsOnly = pathData.map(p => [p.lat, p.lng]);
    const lastPointData = pathData[pathData.length - 1];

 
    polyline = L.polyline(latLngsOnly, {
        color: "#007bff",
        weight: 8,
        smoothFactor: 1.5,
        opacity: 0.7,
        lineJoin: "round",
    }).addTo(map);

    
    polyline.attachedData = pathData;

   
    polyline.on('click', function(e) {
        const clickLocation = e.latlng;
        const data = this.attachedData;
        let closest = data[0];
        let minDistance = Infinity;

        data.forEach(point => {
            const dist = clickLocation.distanceTo(L.latLng(point.lat, point.lng));
            if (dist < minDistance) {
                minDistance = dist;
                closest = point;
            }
        });

        const d = new Date(closest.time);
        const timeStr = d.toLocaleTimeString('el-GR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const dateStr = d.toLocaleDateString('el-GR', { day: '2-digit', month: '2-digit', year: '2-digit' });

        L.popup()
            .setLatLng(clickLocation)
            .setContent(`<b>Time of passage:</b><br>${timeStr}, ${dateStr}`)
            .openOn(map);
    });

    
    if (latLngsOnly.length > 1) {
        decorator = L.polylineDecorator(polyline, {
            patterns: [{
                offset: 25, repeat: 100,
                symbol: L.Symbol.arrowHead({
                    pixelSize: 12, polygon: false,
                    pathOptions: { stroke: true, color: "#fff", weight: 3, opacity: 0.9 },
                }),
            }],
        }).addTo(map);
    }

    let markerColor = "#007bff";
    if (lastPointData.time) {
        const diff = (new Date() - new Date(lastPointData.time)) / 1000 / 60;
        if (diff > 0.1) markerColor = "#ff0000";
    }

    const currentIcon = L.divIcon({
        html: `<div style="background-color: ${markerColor}; width: 16px; height: 16px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 8px rgba(0,0,0,0.4); animation: ${markerColor === "#007bff" ? 'pulse 2s infinite' : 'none'}"></div>`,
        className: "",
        iconSize: [16, 16],
        iconAnchor: [8, 8],
    });

    const dLast = new Date(lastPointData.time);
    const lastUpdateStr = `${dLast.toLocaleTimeString('el-GR')}, ${dLast.toLocaleDateString('el-GR')}`;

    currentMarker = L.marker([lastPointData.lat, lastPointData.lng], { icon: currentIcon })
        .addTo(map)
        .bindPopup(`<b>Last Update:</b><br>${lastUpdateStr}`);
}

async function updatePath(range) {
    try {
        console.log("Fetching historical data for range:", range);
        const response = await fetch(`/api/location/${currentUserID}?range=${range}`);
        const data = await response.json();

        if (data.path && data.path.length > 0) {
            currentPathData = data.path;
            drawRoute(currentPathData);

            map.fitBounds(polyline.getBounds(), { padding: [40, 40], maxZoom: 18 });
        } else {
            console.warn("No historical data found for this range.");
        }
    } catch (err) {
        console.error("Update API Error:", err);
    }
}