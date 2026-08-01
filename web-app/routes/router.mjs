import express from "express";
const router = express.Router();

// Controllers 
const notificationsController = await import("../controllers/notification-controller.mjs");
const liveViewController = await import("../controllers/liveViewController.mjs");
const monitoringController = await import("../controllers/monitoring-controller.mjs");
const homeController = await import("../controllers/home-controller.mjs");
const loginController = await import("../controllers/login-controller.mjs");
const locationController = await import("../controllers/location-controller.mjs");
const commsController = await import("../controllers/comm-controller.mjs");

/* ---------------- AUTH ---------------- */

router.get(
  "/login",
  loginController.checkAuthenticated,
  loginController.showLoginForm
);

router.post("/login", loginController.doLogin);
router.get("/logout", loginController.doLogout);

/* ---------------- HOME ---------------- */

router.get(
  "/home",
  loginController.checkAuthenticated,
  homeController.showHome
);

/* ---------------- LIVE VIEW ---------------- */

router.get(
  "/live-view/:userID",
  loginController.checkAuthenticated,
  loginController.matchUserAndCaregiver,
  liveViewController.showLiveView
);

// /* ---------------- MONITORING ---------------- */

router.get(
  "/monitoring/:userID", 
  loginController.checkAuthenticated,
  loginController.matchUserAndCaregiver,
  monitoringController.showMonitoring
);

// /* ---------------- NOTIFICATIONS / COMM / LOCATION ---------------- */

router.get(
  "/notifications/:userID",
  loginController.checkAuthenticated,
  loginController.matchUserAndCaregiver,
  notificationsController.showNotifications
);

router.get(
  "/communication/:userID",
  loginController.checkAuthenticated,
  loginController.matchUserAndCaregiver,
  commsController.CommsRender
);

router.get(
  "/location/:userID",
  loginController.checkAuthenticated,
  loginController.matchUserAndCaregiver,
  locationController.showLocation
); 
router.get("/api/location/:userID", locationController.getPathData);
export { router };