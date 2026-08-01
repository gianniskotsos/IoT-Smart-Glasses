import express from "express";
import { engine } from "express-handlebars";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import { dirname } from "path";
import { router } from "./routes/router.mjs";
import compression from 'compression';
import sessionConf from "./app-setup/app-setup-session.mjs";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();


app.engine(
  "hbs",
  engine({
    extname: "hbs",
    defaultLayout: "main",
    layoutsDir: path.join(__dirname, "views/layouts"),
    partialsDir: path.join(__dirname, "views/partials"),
    helpers: {
      SplitLines: function (text) {
        if (typeof text !== "string") return "";
        const lines = text.split(",");
        return lines.map((line) => `<div>${line}</div>`).join("");
      },
      ifEquals: function (a, b, options) {
        return a == b ? options.fn(this) : options.inverse(this);
      },
    
     json: function(context) {
  return JSON.stringify(context);
},
    },
  })
);

app.set("view engine", "hbs");
app.set("views", path.join(__dirname, "views"));
app.use(compression());
app.use(express.static(path.join(__dirname, "public")));
app.use(express.urlencoded({ extended: false }));
app.use(sessionConf);
app.use((req, res, next) => {
  if (req.session) {
    res.locals.userId = req.session.caregiverId;
  } else {
    res.locals.userId = null;
  }
  res.locals.mqttBrokerIp = process.env.MQTT_BROKER_IP || "150.140.186.118";
  next();
}); 

app.get("/", (req, res) => {
  res.redirect("/home");
});
app.use("/", router);
app.use("/home", router);


const PORT = process.env.PORT || "3003";
app.listen(PORT, () => {
  console.log(`Connect: http://localhost:${PORT}`);
});