import dotenv from "dotenv";
if (process.env.NODE_ENV !== "production") {
  dotenv.config();
}
const model = await import(
  `../model/${process.env.MODEL}/model-${process.env.MODEL}.mjs`
);
export async function showHome(req, res) {

  const users = await model.getUserList(req.session.caregiverId);
  
  const caregiver = await model.getCaregiverInfo(req.session.caregiverId)
  res.render('home', {
    layout: false,
    title: 'Home',
    caregiver: caregiver,
    users, 
    css: '/css/home.css',
    customJs: '/js/home.js'
  });
}
