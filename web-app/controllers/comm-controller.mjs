import dotenv from "dotenv";
if (process.env.NODE_ENV !== "production") {
  dotenv.config();
}
const db = await import(
  `../model/${process.env.MODEL}/model-${process.env.MODEL}.mjs`
); 


export function CommsRender(req,res) {
    const userID = req.params.userID;
    const userData = db.getUserByID(userID); 
    res.render("communication", {
        layout: "main",
        title: "Communication",
        user: userData,
        activeTab: "communication",
        css: "communication.css",
        customJs: "communication.js",
    });
}