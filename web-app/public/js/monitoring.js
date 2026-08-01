document.addEventListener("DOMContentLoaded", () => {
  if (!window.mqttWorker) {
    console.error("MQTT Worker not found!");
    return;
  }

  const port = window.mqttWorker.port;


port.addEventListener('message', function(e) {
    const { type, topic, payload } = e.data;
    if (type === "MQTT_MESSAGE" && topic.endsWith("/uplink/state")) {
      try {
        const notification = JSON.parse(payload);
        const entity = notification.data[0];
        const data = entity.status.value;
        console.log("Update:", data);
        updateVitalsUI(data);
      } catch (err) {
        console.warn("Payload is not JSON:", payload);
      }
    }
    else if (type === "MQTT_MESSAGE" && topic.endsWith("/uplink/speed")) {
      try {
        const notification = JSON.parse(payload);
        const entity = notification.data[0];
        const data = entity.speed.value;
        console.log("Speed Update:", data);
        updateVitalsUI({speed: data});
      } catch (err) {
        console.warn("Speed payload is not JSON:", payload);
      }
    }
    else if (type === "MQTT_MESSAGE" && topic.endsWith("/uplink/heartRate")) {
      try {
        const notification = JSON.parse(payload);
        const entity = notification.data[0];
        const data = entity.heartRate.value;
        console.log("Heart Rate Update:", data);
        updateVitalsUI({heartRate: data});
      } catch (err) {
        console.warn("Heart Rate payload is not JSON:", payload);
      }
    }
      else if (type === "MQTT_MESSAGE" && topic.endsWith("/uplink/oxygenSaturation")) {
      try {
        const notification = JSON.parse(payload);
        const entity = notification.data[0];
        const data = entity.oxygenSaturation.value;
        console.log("Oxygen Saturation Update:", data);

        updateVitalsUI({oxygenSaturation: data});
      } catch (err) {
        console.warn("Oxygen Saturation payload is not JSON:", payload);
      }
    }
  });
});


function updateVitalsUI(data) {

  // Battery
  if (data.battery !== undefined) {
    const el = document.querySelector(".battery");
    el.textContent = data.battery + "%";
    applyStatusColor(el, data.battery, 30, 15, false);
  }

  // CPU
  if (data.cpu_percent !== undefined) {
    const el = document.querySelector(".cpu");
    el.textContent = data.cpu_percent + "%";
    applyStatusColor(el, data.cpu_percent, 70, 90);
  }

  // RAM & Temp
  if (data.mem_percent !== undefined) {
    const el = document.querySelector(".ram");
    el.textContent = data.mem_percent + "%";
    applyStatusColor(el, data.mem_percent, 70, 90);
  }
  if (data.temp_c !== undefined) {
    const el = document.querySelector(".temp");
    el.textContent = data.temp_c + "°C";
    applyStatusColor(el, data.temp_c, 60, 80);
  }
  if (data.uptime_sec !== undefined) {
    const el = document.querySelector(".runtime");
    const hours = Math.floor(data.uptime_sec / 3600);
    const minutes = Math.floor((data.uptime_sec % 3600) / 60);
    el.textContent = `${hours}h ${minutes}m`;
  }
  else if (data.heartRate !== undefined) {
    const el = document.querySelector(".heartRate");
    el.textContent = data.heartRate + " bpm";
    applyStatusColor(el, data.heartRate, 100, 120);
  }
  else if (data.oxygenSaturation !== undefined) {
    const el = document.querySelector(".oxygenSaturation");
    el.textContent = data.oxygenSaturation + "%";
    applyStatusColor(el, data.oxygenSaturation, 95, 90, false);
  }

  else if (data.speed !== undefined) {
    document.querySelector(".speed").textContent = parseFloat(data.speed).toFixed(2)+" km/h";
    const activity = getActivityFromSpeed(data.speed);
    const el = document.querySelector(".activity");
    const activity_change = updateActivityIcon(activity);
     if (activity_change) {
        el.textContent = activity;
  }
  }

}


function getActivityFromSpeed(speed) {
  if (speed <= 0.5) return "Still";
  if (speed <= 2.0) return "Slow walking";
  if (speed <= 5.5) return "Walking";
  if (speed <= 8.0) return "Fast walking";
  return "Transit";
}


function getActivityIcon(activity) {
  switch (activity) {
    case "Still":
      return "fa-solid fa-person";
    case "Slow walking":
      return "fa-solid fa-person-walking";
    case "Walking":
      return "fa-solid fa-person-walking";
    case "Fast walking":
      return "fa-solid fa-person-running";
    case "Transit":
      return "fa-solid fa-car";
    default:
      return "fa-solid fa-person";
  }
}




let lastActivityIconChange = 0;
const ICON_CHANGE_TIMEOUT = 10000;


function updateActivityIcon(activity) {
  const now = Date.now();
  if (now - lastActivityIconChange < ICON_CHANGE_TIMEOUT) {
    console.log("Icon change skipped to prevent rapid updates");
    return false; 
  }

  const iconElement = document.getElementById("activityIcon");

  if (!iconElement) return;

  const newIcon = getActivityIcon(activity);
  iconElement.className = newIcon;
  lastActivityIconChange = now;

  return true; 
}


function applyStatusColor(
  element,
  value,
  warning,
  critical,
  isLowerBetter = true,
) {
  if (!element) return;

  element.classList.remove(
    "status-normal",
    "status-warning",
    "status-critical",
  );

  if (isLowerBetter) {
    if (value >= critical) element.classList.add("status-critical");
    else if (value >= warning) element.classList.add("status-warning");
    else element.classList.add("status-normal");
  } else {
    if (value <= critical) element.classList.add("status-critical");
    else if (value <= warning) element.classList.add("status-warning");
    else element.classList.add("status-normal");
  }
}


const toggleBtn = document.getElementById('toggle-btn');
  const iframe = document.getElementById('fitnessIframe');

  const urls = {
    today: "http://labserver.sense-campus.gr:8087/d-solo/df8pa87y4308wb/fitness-data?from=now-1d&to=now&timezone=browser&refresh=5s&orgId=2&theme=light&panelId=2&__feature.dashboardSceneSolo",
    lastWeek: "http://labserver.sense-campus.gr:8087/d-solo/df8pa87y4308wb/fitness-data?from=now-1d&to=now&timezone=browser&refresh=5s&tab=queries&orgId=2&theme=light&panelId=3&__feature.dashboardSceneSolo"

  };

  let showingToday = true;

  toggleBtn.addEventListener('click', () => {
    if(showingToday){
      iframe.src = urls.lastWeek;
      toggleBtn.textContent = "See Today";
      showingToday = false;
    } else {
      iframe.src = urls.today;
      toggleBtn.textContent = "See Last Week";
      showingToday = true;
    }
  });

/**
 * Toggle collapsible sections (User's Graphs / System's Graphs)
 */
function toggleSection(header) {
  header.classList.toggle('collapsed');
  const content = header.nextElementSibling;
  content.classList.toggle('collapsed');
}