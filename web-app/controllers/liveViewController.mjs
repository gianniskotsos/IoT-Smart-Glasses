import dotenv from "dotenv";
if (process.env.NODE_ENV !== "production") {
  dotenv.config();
}
const db = await import(
  `../model/${process.env.MODEL}/model-${process.env.MODEL}.mjs`
);
import { getStreamURL } from "../services/vms-service.mjs";


export function showLiveView(req,res) {
    const user = db.getUserByID(req.params.userID);
    
    res.render("live-view", {
        layout: "main",
        css : "live-view.css",
        customJs :"live-view.js",
        user,
        title : "Live View",
        activeTab: "live-view",
        buttonText: "Turn Camera On",
        GLASS_STREAM_URL: getStreamURL(req.params.userID),
    });
}
    