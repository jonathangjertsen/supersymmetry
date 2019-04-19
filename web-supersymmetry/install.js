const db = require('./db');

db.serialize(function() {
    db.run("PRAGMA writable_schema = 1");
    db.run("delete from sqlite_master where type in ('table', 'index', 'trigger')");
    db.run("PRAGMA writable_schema = 0");
    db.run("VACUUM");
    db.run("PRAGMA INTEGRITY_CHECK");
    db.run("CREATE TABLE games (gid TEXT PRIMARY KEY, state TEXT)");
    db.run("CREATE TABLE players (gid TEXT, username TEXT, color INT)");
});

db.close();
