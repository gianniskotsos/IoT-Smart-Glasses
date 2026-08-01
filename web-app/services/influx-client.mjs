import { InfluxDB } from "@influxdata/influxdb-client";

const token = process.env.INFLUXDB_TOKEN;
const org = process.env.INFLUXDB_ORG;
const url = process.env.INFLUXDB_URL;
const client = new InfluxDB({ url, token });

const queryApi = client.getQueryApi(org);

export { queryApi };
