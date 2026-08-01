import dotenv from "dotenv";
import { queryApi } from "../services/influx-client.mjs";
import { flux,fluxExpression } from '@influxdata/influxdb-client';
if (process.env.NODE_ENV !== "production") {
  dotenv.config();
}
const db = await import(
  `../model/${process.env.MODEL}/model-${process.env.MODEL}.mjs`
);
export const showLocation = async (req, res) => {
  const deviceId = req.params.userID;
  const fluxQuery = flux`
      from(bucket: "${process.env.INFLUXDB_BUCKET}")
        |> range(start: 0)  
        |> filter(fn: (r) => r["_measurement"] == "location_data")
        |> filter(fn: (r) => r["device_id"] == ${deviceId})
        |> last() 
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    `;

  try {
    let data = await queryApi.collectRows(fluxQuery);
    const userData = await db.getUserByID(deviceId);

    
    const path = data
      .filter(row => row.latitude != null && row.longitude != null)
      .map(row => ({
        lat: row.latitude,
        lng: row.longitude,
        time: row._time
      })); 
    
    let currentLocation = null;
    if (path.length > 0) {
      const lastPoint = path[path.length - 1];
      currentLocation = { lat: lastPoint.lat, lng: lastPoint.lng };
    }

    res.render("location", {
      layout: "main",
      title: "Live Location & Route",
      user: userData,
      activeTab: "location",
      css: "location.css",
      customJs: "location.js",
      pathData: JSON.stringify(path) || null, 
      currentLocation:  JSON.stringify(currentLocation) || null,
      error: data.length === 0 ? "No data found" : undefined
    });

  } catch (error) {
    console.error("InfluxDB Error:", error);
    res.status(500).send("Error occurred while fetching data from the database.");
  }
};

export const getPathData = async (req, res) => {
  const { userID } = req.params;
  const { range } = req.query;

  let fluxQuery;
  
  if (!range || range === '0') {
    
    fluxQuery = flux`
      from(bucket: "${process.env.INFLUXDB_BUCKET}")
        |> range(start: 0) 
        |> filter(fn: (r) => r["_measurement"] == "location_data")
        |> filter(fn: (r) => r["device_id"] == ${userID})
        |> last()
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    `;
  } else {
    fluxQuery = flux`
      from(bucket: "${process.env.INFLUXDB_BUCKET}")
        |> range(start: -${fluxExpression(range)})
        |> filter(fn: (r) => r["_measurement"] == "location_data")
        |> filter(fn: (r) => r["device_id"] == ${userID})
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> sort(columns: ["_time"], desc: false)
    `;
  }

  try {
    const data = await queryApi.collectRows(fluxQuery);
    if (data.length === 0) {
        fluxQuery = flux`
      from(bucket: "${process.env.INFLUXDB_BUCKET}")
        |> range(start: 0) 
        |> filter(fn: (r) => r["_measurement"] == "location_data")
        |> filter(fn: (r) => r["device_id"] == ${userID})
        |> last()
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    `;
    const lastData = await queryApi.collectRows(fluxQuery);
      return res.json({ path: lastData.map(row => ({
        lat: row.latitude,
        lng: row.longitude,
        time: row._time
      })) });
    } 
    const path = data.map(row => ({
      lat: row.latitude,
      lng: row.longitude,
      time: row._time
    }));

    res.json({ path });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};