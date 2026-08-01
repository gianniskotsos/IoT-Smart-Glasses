import session from "express-session";
import dotenv from "dotenv";
dotenv.config();
const sessionConf = session({
  secret: process.env.SESSION_SECRET,
  cookie: { maxAge: 3600000, sameSite: true },
  resave: false,
  saveUninitialized: false,
});

export default sessionConf;
