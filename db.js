const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('SuperSymmetry.db');
module.exports = db;
