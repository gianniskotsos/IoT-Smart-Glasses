import dotenv from "dotenv";

if (process.env.NODE_ENV !== "production") {
  dotenv.config();
}
const userModel = await import(
  `../model/${process.env.MODEL}/model-${process.env.MODEL}.mjs`
);
/**
 * GET /login
 */
export function showLoginForm(req, res) {
  res.render("login", {
    title: "Σύνδεση",
    css: "css/login.css",
    customJs: "/js/login.js",
    layout: false, //
    metaDescription: "Login to access the application.",
  });
}

/**
 * POST /login
 */
export async function doLogin(req, res) {
  const { email, password } = req.body;
  console.log("Login attempt with email:", email);
  if (!email || !password) {
    return res.render("login", {
      title: "Σύνδεση",
      css: "css/login.css",
      layout: false,
      message: "Please fill in email and password",
    });
  }

  try {
   
    const user = await userModel.getCaregiverByEmail(email);

    if (!user || !user.email) {
      console.log("User not found for email:", email);
      return res.render("login", {
        title: "Σύνδεση",
        css: "css/login.css",
        layout: false,
        message: "No user found with that email",
      });
    }

    
    if (user.password !== password) {
      console.log("Incorrect password for email:", email);
      return res.render("login", {
        title: "Σύνδεση",
        css: "css/login.css",
        layout: false,
        message: "The password is incorrect",
      });
    }

    
    req.session.caregiverId = user.ID;
    console.log("Logged in user ID :", req.session.caregiverId);
    const redirectTo = req.session.originalUrl || "/home";
    console.log("Redirecting to:", redirectTo);
    delete req.session.originalUrl;

    res.redirect(redirectTo);
  } catch (error) {
    console.error(error);
    res.render("login", {
      title: "Σύνδεση",
      css: "css/login.css",
      layout: false,
      message: "Error occurred during login",
    });
  }
}

/**
 * GET /logout
 */
export function doLogout(req, res) {
  req.session.destroy(() => {
    res.redirect("/login");
  });
}


export function checkAuthenticated(req, res, next) {
  if (req.session.caregiverId || req.originalUrl === "/login") {
    console.log("User is authenticated");
    return next();
  }
  else {
    req.session.originalUrl = req.originalUrl;
    res.redirect("/login");
  }
}
  
export function matchUserAndCaregiver(req, res, next) {
  const userID = req.params.userID;
  const caregiverID = req.session.caregiverId; 
  if (userModel.matchUserAndCaregiver(userID, caregiverID)) {
    console.log(`User ${userID} belongs to caregiver ${caregiverID}`);
    return next();
  } else {
    console.log(`User ${userID} does NOT belong to caregiver ${caregiverID}`);
    return res.status(403).send("You do not have access to this user.");
  } }