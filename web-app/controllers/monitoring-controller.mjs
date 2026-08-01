


import dotenv from "dotenv";
if (process.env.NODE_ENV !== "production") {
  dotenv.config();
}
const db = await import(
  `../model/${process.env.MODEL}/model-${process.env.MODEL}.mjs`
);  
export  function showMonitoring(req, res) {
  try {
    const userID = req.params.userID;
    const userData = db.getUserByID(userID); 
    res.render("monitoring",{
      layout: "main",
      user: userData,
      title: "Monitoring",
      activeTab: "monitoring",
      css:"monitoring.css",
      customJs:"monitoring.js"});

  } catch (err) {
    console.error(err);
    res.status(500).send("Error fetching monitoring data");
  }
}