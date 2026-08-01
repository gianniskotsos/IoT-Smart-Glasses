import dotenv from "dotenv";
if (process.env.NODE_ENV !== "production") {
  dotenv.config();
}
const db = await import(
  `../model/${process.env.MODEL}/model-${process.env.MODEL}.mjs`
); 

export function showNotifications(req,res) {
  const userID = req.params.userID;
  const userData = db.getUserByID(userID); 
  res.render("notifications", {
    layout: "main",
    title: "Notifications",
    user: userData,
    activeTab: "notifications",
    css: "notifications.css",
    customJs: "notifications.js"
  });
 }