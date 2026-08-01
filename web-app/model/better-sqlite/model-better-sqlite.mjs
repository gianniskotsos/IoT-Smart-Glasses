"use strict";

import { default as bettersqlite3 } from "better-sqlite3";
const db = new bettersqlite3("model/db/web_sqlite_test.db", {
  fileMustExist: true,
});
export const getUserList = (caregiverID) => {
  const stmt = db.prepare("SELECT * FROM user WHERE caregiver_ID = ?");
  return stmt.all(caregiverID);
};
export const getUserByID = (userID) => {
  const stmt = db.prepare("SELECT * FROM user WHERE userID = ?");
  return stmt.get(userID);
};
export const getCaregiverByEmail = (email) => {
  try {
    const stmt = db.prepare("SELECT * FROM caregiver WHERE email = ?");
    return stmt.get(email);
  } catch (error) {
    console.error("Error fetching caregiver by email:", error);
    throw error;
  }
}
export const getCaregiverInfo = (caregiverID) => {
  console.log("caregiverID:", caregiverID, typeof caregiverID); 
  const stmt = db.prepare("SELECT * FROM caregiver WHERE ID = ?");
  const caregiver = stmt.get(caregiverID);
  return caregiver;}
  
export const matchUserAndCaregiver = (userID, caregiverID) => { 
  const stmt = db.prepare("SELECT * FROM user WHERE userID = ? AND caregiver_ID = ?");
  const user = stmt.get(userID, caregiverID);
  return !!user; 
} 

