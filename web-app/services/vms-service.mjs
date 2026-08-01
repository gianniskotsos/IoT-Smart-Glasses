import dotenv from "dotenv";

dotenv.config();


export function getStreamURL(userID) {

   
    return "http://" + process.env.VMS_IP + "/stream";
}