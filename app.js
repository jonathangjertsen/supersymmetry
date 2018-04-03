const express = require('express');
const app = express();
const http = require('http').Server(app);
const crypto = require('crypto');
const io = require('socket.io')(http);
const db = require('./db');

app.use(express.static('public'));

io.on('connection', function(socket){
    socket.on('requestGame', function(game) {
        const query = `SELECT gid, state FROM games WHERE gid = ?`;
        db.get(query, [game], (err, row) => {
            if (err) {
                console.error(err);
                return;
            }

            socket.emit('requestGame', row);
            socket.join(game);
        });
    });

    socket.on('newGame', function(game) {
        const query = "INSERT INTO games(gid, state) VALUES(?, ?)";
        crypto.randomBytes(8, (err, buf) => {
            if (err) {
                console.error(err);
                return;
            }
            const gid = buf.toString('hex');

            db.get(query, [gid, JSON.stringify(game)], (err) => {
                if (err) {
                    console.error(err);
                    return;
                }

                socket.emit('newGame', gid);
                socket.join(gid);
            });
        });
    });

    socket.on('move', function(data) {
        const query = "UPDATE games SET state = ? WHERE gid = ?";
        db.run(query, [JSON.stringify(data.state), data.gid], function(err) {
            if (err) {
                console.error(err);
                return;
            }

            socket.to(data.gid).emit('newGameState', {
                gid: data.gid,
                state: JSON.stringify(data.state)
            });
        });
    });
});

http.listen(3000, function(){
    console.log('listening on *:3000');
});
