class Player {
    constructor(username, color) {
        this.username = username;
        this.color = color;
        this.highlightedPiece = null;
    }
}

class Board {
    constructor(n) {
        this.n = n;

        this.drawing = {
            ctx: null,
            enabled: false,
            unit: 20,
            xOffset: 0,
            yOffset: 0,
            highlightAllowed: true,
            debug: false
        };
        this.drawing.inherentXOffset = 0;//- this.drawing.unit * (2.63 * n);

        this.codes = {
            forbidden: -1,
            free: 0,
            black: 1,
            green: 2,
            yellow: 3,
            red: 4,
            white: 5,
            blue: 6
        };

        this.colors = {
            background: tinycolor('#ffffff').brighten(25),
            forbidden: tinycolor('#ff9900').brighten(25),
            free: tinycolor('#99ffcc'),
            black: tinycolor('#000000'),
            green: tinycolor('#009933'),
            yellow: tinycolor('#ffff00'),
            red: tinycolor('#cc0000'),
            white: tinycolor('#cccccc'),
            blue: tinycolor('#3333ff')
        };

        this.game = {
            players: [],
            currentPlayer: null,
            hops: 0,
            didSingleHop: false,
            rules: [
                {
                    id: 'OutOfRepresentation',
                    required: true,
                    enabled: true,
                    description: 'Can not move out of bounds',
                    check: (i0, j0, i, j) => this.inBounds(i, j)
                },
                {
                    id: 'OutOfBounds',
                    required: true,
                    enabled: true,
                    description: 'Can not move out of bounds',
                    check: (i0, j0, i, j) => this.board[i][j] !== this.codes.forbidden
                },
                {
                    id: 'SingleHopIsFinal',
                    required: true,
                    enabled: true,
                    description: 'Can not move after moving by only one spot',
                    check: (i0, j0, i, j) => {
                        return !this.game.didSingleHop;
                    }
                },
                {
                    id: 'Line',
                    required: false,
                    enabled: true,
                    description: 'Must move in a line',
                    check: (i0, j0, i, j) => i === i0 || j === j0 || (i - i0 === j0 - j)
                },
                {
                    id: 'LineOrDiagonal',
                    required: false,
                    enabled: true,
                    description: 'Must move in a line or along the diagonal',
                    check: (i0, j0, i, j) => i === i0 || j === j0 || (i - i0 === j0 - j) || (i - i0 === j - j0)
                },
                {
                    id: 'Unoccupied',
                    required: false,
                    enabled: true,
                    description: 'Must land on an unoccupied slot (uncheck to allow a piece to be "captured" by landing on it)',
                    check: (i0, j0, i, j) => !this.occupied(i, j)
                },
                {
                    id: 'OnePieceOver',
                    required: false,
                    enabled: false,
                    description: 'Can not jump over multiple pieces in a jump',
                    check: (i0, j0, i, j) => {
                        const iMax = Math.max(i, i0), iMin = Math.min(i, i0), iD = Math.abs(i - i0);
                        const jMax = Math.max(j, j0), jMin = Math.min(j, j0), jD = Math.abs(j - j0);
                        let numOccupied = 0;
                        if (i === i0) {
                            for (let s = 1; s < jD; s++) {
                                numOccupied += this.occupied(i, jMin + s);
                            }
                        } else if (j === j0) {
                            for (let s = 1; s < iD; s++) {
                                numOccupied += this.occupied(iMin + s, j);
                            }
                        } else if (i - i0 === j0 - j) {
                            for (let s = 1; s < iD; s++) {
                                numOccupied += this.occupied(iMin + s, jMax - s);
                            }
                        } else if (i - i0 === j - j0) {
                            for (let s = 1; s < iD; s++) {
                                numOccupied += this.occupied(iMin + s, jMin + s);
                            }
                        } else {
                            return false;
                        }

                        return numOccupied <= 1;
                    }
                },
                {
                    id: 'SuperSymmetry',
                    required: false,
                    enabled: true,
                    description: 'Move must be mirror symmetric',
                    check: (i0, j0, i, j) => {
                        const iMax = Math.max(i, i0), iMin = Math.min(i, i0), iD = Math.abs(i - i0);
                        const jMax = Math.max(j, j0), jMin = Math.min(j, j0), jD = Math.abs(j - j0);
                        if (i === i0) {
                            for (let s = 1; s < jD; s++) {
                                if (this.occupied(i, jMin + s) !== this.occupied(i, jMax - s)) {
                                    return false;
                                }
                            }
                        } else if (j === j0) {
                            for (let s = 1; s < iD; s++) {
                                if (this.occupied(iMin + s, j) !== this.occupied(iMax - s, j)) {
                                    return false;
                                }
                            }
                        } else if (i - i0 === j0 - j) {
                            for (let s = 1; s < iD; s++) {
                                if (this.occupied(iMin + s, jMax - s) !== this.occupied(iMax - s, jMin + s)) {
                                    return false;
                                }
                            }
                        } else if (i - i0 === j - j0) {
                            for (let s = 1; s < iD; s++) {
                                if (this.occupied(iMin + s, jMin + s) !== this.occupied(iMax - s, jMax - s)) {
                                    return false;
                                }
                            }
                        } else {
                            return false;
                        }

                        return true;
                    }
                },
                {
                    id: 'NoGaps',
                    enabled: true,
                    required: false,
                    description: 'Can not cross gaps without jumping over a piece',
                    check: (i0, j0, i, j) => {
                        const iMax = Math.max(i, i0), iMin = Math.min(i, i0), iD = Math.abs(i - i0);
                        const jMax = Math.max(j, j0), jMin = Math.min(j, j0), jD = Math.abs(j - j0);

                        // Allow single hops
                        if (this.game.hops === 0 && jD <= 1 && iD <= 1) {
                            return true;
                        }

                        // Otherwise there must exist at least one occupied slot in the line
                        if (i === i0) {
                            for (let s = 1; s < jD; s++) {
                                if (this.occupied(i, jMin + s)) {
                                    return true;
                                }
                            }
                        } else if (j === j0) {
                            for (let s = 1; s < iD; s++) {
                                if (this.occupied(iMin + s, j)) {
                                    return true;
                                }
                            }
                        } else if (i - i0 === j0 - j) {
                            for (let s = 1; s < iD; s++) {
                                if (this.occupied(iMin + s, jMax - s)) {
                                    return true;
                                }
                            }
                        } else if (i - i0 === j - j0) {
                            for (let s = 1; s < iD; s++) {
                                if (this.occupied(iMin + s, jMin + s)) {
                                    return true;
                                }
                            }
                        }
                        return false;
                    }
                },
                {
                    id: 'NoEnemyLanding',
                    enabled: false,
                    required: true,
                    description: 'Can not land in enemy territory, even temporarily',
                    check: this.inEnemyTerritory.bind(this)
                }
            ],
            destinationRules: [
                {
                    id: 'NoEnemyFinishing',
                    enabled: true,
                    required: false,
                    description: 'Can not finish in enemy territory',
                    check: this.inEnemyTerritory.bind(this)
                }
            ]
        };
    }

    inEnemyTerritory(i, j) {
        const playerColor = this.game.currentPlayer.color;
        const locationColor = this.nameFromCode(this.board[i][j]);

        if (locationColor === 'free') {
            return true;
        }

        if (playerColor === 'red' || playerColor === 'black') {
            return locationColor === 'red' || locationColor === 'black';
        }

        if (playerColor === 'green' || playerColor === 'white') {
            return locationColor === 'green' || locationColor === 'green';
        }

        if (playerColor === 'yellow' || playerColor === 'blue') {
            return locationColor === 'yellow' || locationColor === 'blue';
        }

        return false;
    }

    occupied(i, j) {
        return this.locations[i][j] !== null;
    }

    init() {
        this.drawing.enabled = true;
        this.initBoard();
        this.initLocations();
        this.save();
        this.drawBoard();
        this.drawAllPieces();
        this.drawing.ctx.canvas.onclick = this.click.bind(this);
        this.drawing.ctx.canvas.onmousemove = this.hover.bind(this);
    }

    save() {
        this.backup = {
            board: JSON.parse(JSON.stringify(this.board)),
            locations: JSON.parse(JSON.stringify(this.locations))
        }
    }

    load() {
        this.board = this.backup.board;
        this.locations = this.backup.locations;
    }

    mousePos(event) {
        const canvas = this.drawing.ctx.canvas;
        const rect = canvas.getBoundingClientRect();
        let x = (event.clientX - rect.left) * (canvas.width / rect.width), y = (event.clientY - rect.top) * (canvas.width / rect.width);

        return {
            i: Math.ceil(this.i(x, y)),
            j: Math.floor(this.j(x, y))
        }
    }

    hover(event) {
        const mousePos = this.mousePos(event);
        this._hover(mousePos.i, mousePos.j);
    }

    _hover(i, j) {
        this.drawBoard();
        this.drawAllPieces();
        const player = this.game.currentPlayer;
        if (player && player.highlightedPiece) {
            this._clickedOwnPiece(player.highlightedPiece.i, player.highlightedPiece.j);
        }
        if (this.inBounds(i, j) && this.board[i][j] !== this.codes.forbidden) {
            this.highlight(i, j, tinycolor('yellow'));
        }
    }

    inBounds(i, j) {
        return i >= 0 && i < this.width && j >= 0 && j < this.width;
    }

    click(event) {
        const mousePos = this.mousePos(event);
        this._click(mousePos.i, mousePos.j);
    }

    _click(i, j) {
        if (!this.game.currentPlayer) {
            this.reportError("No current player");
            return;
        }

        const isOwnPiece = this.nameFromCode(this.locations[i][j]) === this.game.currentPlayer.color;

        // If something is highlighted already
        if (this.game.currentPlayer.highlightedPiece) {
            if (!isOwnPiece) {
                this.tryMove(i, j);
                return;
            }
            this.resetMoves();
        }

        // If nothing is highlighted
        this.save();
        if (!isOwnPiece) {
            this.reportError("Must choose an own piece");
            return;
        }
        this._clickedOwnPiece(i, j);
    }

    tryMove(i, j) {
        const prevPiece = this.game.currentPlayer.highlightedPiece;
        for (let r = 0; r < this.game.rules.length; r++) {
            const rule = this.game.rules[r];
            if (rule.enabled && !rule.check(prevPiece.i, prevPiece.j, i, j)) {
                this.reportError(`${rule.description}, tried (${prevPiece.i}, ${prevPiece.j}) --> (${i}, ${j})`);
                return;
            }
        }
        this.movePiece(prevPiece.i, prevPiece.j, i, j);
        this._clickedOwnPiece(i, j);
    }

    _clickedOwnPiece(i, j) {
        this.drawBoard();
        this.drawAllPieces();
        this.highlight(i, j, tinycolor('orange').darken(10));
        this.game.currentPlayer.highlightedPiece = { i: i, j: j };
        if (this.drawing.highlightAllowed) {
            this.forBoard((iMaybe, jMaybe) => {
                for (let r = 0; r < this.game.rules.length; r++) {
                    if (this.game.rules[r].enabled && !this.game.rules[r].check(i, j, iMaybe, jMaybe)) {
                        return;
                    }
                }
                this.highlight(iMaybe, jMaybe, tinycolor('green'));
            });
        }
    }

    reportError(err) {
        console.error(err);
    }

    doMoves() {
        if (this.game.currentPlayer && this.game.currentPlayer.highlightedPiece) {
            const piece = this.game.currentPlayer.highlightedPiece;
            for (let r = 0; r < this.game.destinationRules.length; r++) {
                let rule = this.game.destinationRules[r];
                if (rule.enabled && !rule.check(piece.i, piece.j)) {
                    this.reportError(`Error: ${rule.description}, tried landing on (${piece.i}, ${piece.j})`);
                    this.resetMoves();
                    return;
                }
            }

            this.game.currentPlayer.highlightedPiece = null;
            this.drawBoard();
            this.drawAllPieces();
            let next = this.playerIdx(this.game.currentPlayer.color) + 1;
            if (next >= this.game.players.length) {
                next = 0;
            }
            this.game.currentPlayer = this.game.players[next];
            this.game.hops = 0;
            this.game.didSingleHop = false;
            this.save();
        }
    }

    resetMoves() {
        this.load();
        this.game.currentPlayer.highlightedPiece = null;
        this.game.hops = 0;
        this.game.didSingleHop = false;
        this.drawBoard();
        this.drawAllPieces();
    }

    get width() {
        return this.n * 4 + 1;
    }

    nameFromCode(c) {
        switch (c) {
            case -1:
                return 'forbidden';
            case 0:
                return 'free';
            case 1:
                return 'black';
            case 2:
                return 'green';
            case 3:
                return 'yellow';
            case 4:
                return 'red';
            case 5:
                return 'white';
            case 6:
                return 'blue';
            case null:
                return null;
            default:
                throw `Invalid code ${c}`;
        }
    }

    initBoard() {
        const n = this.n;
        const board = [];
        const width = this.width;
        const codes = this.codes;
        for (let i = 0; i < width; i++) {
            const line = [];
            for (let j = 0; j < width; j++) {
                // Lower left corner
                if ((i < 2 * n + 1 && j < n) || (j < 2 * n + 1 && i < n)) {
                    line.push(codes.forbidden);
                    continue;
                }

                // Lower right and upper left corners
                if ((i >= 3 * n + 1 && j < n) || (j >= 3 * n + 1 && i < n)) {
                    line.push(codes.forbidden);
                    continue;
                }

                // Top right corner
                if ((i >= 2 * n && j >= 3 * n + 1) || (j >= 2 * n && i >= 3 * n + 1)) {
                    line.push(codes.forbidden);
                    continue;
                }

                // Upper right free area
                if ((i >= n && i < 2 * n + 1 && j >= 2 * n && j < 3 * n + 1)) {
                    line.push(codes.free);
                    continue;
                }

                // Lower right free area
                if (i >= 2 * n && i < 3 * n + 1 && j >= n && j < 2 * n + 1) {
                    line.push(codes.free);
                    continue;
                }

                // Black and free area
                if (i >= n && i < 2 * n && j >= n && j < 2 * n) {
                    const x = i - n, y = j - n;
                    line.push(x + y < n ? codes.black : codes.free);
                    continue;
                }

                // Blue and forbidden area
                if (i >= 2 * n + 1 && i < 3 * n + 1 && j < n) {
                    const w = 3 * n - i, z = n - j - 1;
                    line.push(w + z < n ? codes.blue : codes.forbidden);
                    continue;
                }

                // White and forbidden area
                if (i >= 3 * n + 1 && j >= n && j < 2 * n) {
                    const x = i - (3 * n + 1), y = j - n;
                    line.push(x + y < n ? codes.white : codes.forbidden);
                    continue;
                }

                // Red and free area
                if (i >= 2 * n + 1 && i < 3 * n + 1 && j >= 2 * n + 1 && j < 3 * n + 1) {
                    const w = 3 * n - i, z = 3 * n - j;
                    line.push(w + z < n ? codes.red : codes.free);
                    continue;
                }

                // Yellow and forbidden area
                if (i >= n && i < 2 * n && j >= 3 * n + 1) {
                    const x = i - n, y = j - (3 * n + 1);
                    line.push(x + y < n ? codes.yellow : codes.forbidden);
                    continue;
                }

                // Green and forbidden area
                if (i < n && j >= 2 * n + 1 && j < 3 * n + 1) {
                    const w = n - i - 1, z = 3 * n - j;
                    line.push(w + z < n ? codes.green : codes.forbidden);
                    continue;
                }

                throw `Failed to consider values (i=${i}, j=${j})`;
            }
            board.push(line);
        }
        this.board = board;
    }

    get fullXOffset() {
        return this.drawing.xOffset + this.drawing.inherentXOffset;
    }

    x(i, j) {
        if (this.drawing.debug) {
            return i * this.drawing.unit;
        }
        return i * this.drawing.unit + j * this.drawing.unit / 2 + this.fullXOffset;
    }

    y(i, j) {
        if (this.drawing.debug) {
            return j * this.drawing.unit;
        }
        return j * this.drawing.unit * Math.sqrt(3) / 2 + this.drawing.yOffset;
    }

    i(x, y) {
        if (this.drawing.debug) {
            return (x - this.fullXOffset) / this.drawing.unit;
        }
        // x = i*u+j*u/2+x_off+x_off2
        // y = j*u+sqrt(3)/2+y_off
        // i*u = x - j*u /2 - x_off - x_off2
        // j*u = y - sqrt(3)/2 - y_off
        const result = (x - this.fullXOffset) / this.drawing.unit - this.j(x, y) / 2;

        // ???
        return result;
    }

    j(x, y) {
        if (this.drawing.debug) {
            return (y - this.drawing.yOffset) / this.drawing.unit
        }
        const result = (y - Math.sqrt(3)/2- this.drawing.yOffset) / this.drawing.unit;

        // ???
        return result + 1;
    }

    forBoard(func) {
        const width = this.width;
        for (let i = 0; i < width; i++) {
            for (let j = 0; j < width; j++) {
                func(i, j)
            }
        }
    }

    copycolor(color) {
        return tinycolor(color.toHexString());
    }

    drawBoard() {
        const codes = this.codes;
        const ctx = this.drawing.ctx;
        ctx.save();
        if (!this.drawing.debug) {
            // Background
            ctx.fillStyle = this.colors.background.toHexString();
            ctx.fillRect(0, 0, this.width * this.drawing.unit * 2, this.width * this.drawing.unit * 2);

            // Board
            ctx.beginPath();
            const mid = this.drawing.unit * (2 * this.n + 1);
            const gradient = this.drawing.ctx.createRadialGradient(mid*0.3, mid*0.3, 0, mid, mid, mid);
            gradient.addColorStop(1, this.copycolor(this.colors.forbidden).darken(10));
            gradient.addColorStop(0, this.copycolor(this.colors.forbidden).brighten(35));
            ctx.fillStyle = gradient;
            ctx.strokeStyle = 'black';
            ctx.lineWidth = 5;
            ctx.moveTo(this.x(this.n-1, this.n-1), this.y(this.n-1, this.n-1));
            const n = this.n;
            const path = [
                [2*n, n-1],
                [3*n+1, -2],
                [3*n+1, n-1],
                [4*n+2, n-1],
                [3*n+1, 2*n],
                [3*n+1, 3*n+1],
                [2*n, 3*n+1],
                [n-1, 4*n+2],
                [n-1, 3*n+1],
                [-2, 3*n+1],
                [n-1, 2*n],
                [n-1, n-1],
                [2*n, n-1]
            ];
            for (let p = 0; p < path.length; p++) {
                ctx.lineTo(this.x(path[p][0], path[p][1]), this.y(path[p][0], path[p][1]));
            }
            ctx.stroke();
            ctx.fill();
        }

        // Places
        this.forBoard((i, j) => {
            const code = this.board[i][j];
            if (code === codes.forbidden && !this.drawing.debug) {
                return;
            }

            ctx.save();
            ctx.beginPath();
            ctx.lineWidth = 0.4;
            const x = this.x(i, j), y = this.y(i, j), r = this.drawing.unit / 4;
            const gradient = this.drawing.ctx.createRadialGradient(x-r/3, y-r/3, 0, x, y, r);
            gradient.addColorStop(1, this.placeColor(code));
            gradient.addColorStop(0, this.pieceColor(code));
            ctx.fillStyle = gradient;
            ctx.arc(x, y, r, 0, 2 * Math.PI);
            ctx.fill();
            ctx.stroke();
            ctx.restore();
        });
        ctx.restore();
    }

    pieceColor(code) {
        return this.colors[this.nameFromCode(code)];
    }

    placeColor(code) {
        return tinycolor(this.colors[this.nameFromCode(code)].toHexString()).brighten(25).toHexString();
    }

    drawPiece(i, j, color) {
        this.drawing.ctx.save();
        const x = this.x(i, j), y = this.y(i, j), r = this.drawing.unit / 3;
        this.drawing.ctx.beginPath();
        const gradient = this.drawing.ctx.createRadialGradient(x-r/3, y-r/3, 0, x, y, r);
        gradient.addColorStop(1, this.pieceColor(color));
        gradient.addColorStop(0, this.placeColor(color));
        this.drawing.ctx.fillStyle = gradient;
        this.drawing.ctx.arc(x, y, r, 0, 2 * Math.PI);
        this.drawing.ctx.fill();
        this.drawing.ctx.stroke();
        this.drawing.ctx.restore();
    }

    drawAllPieces() {
        this.forBoard((i, j) => {
            if (this.locations[i][j] > this.codes.free) {
                this.drawPiece(i, j, this.locations[i][j]);
            }
        });
    }

    placePiece(i, j, code) {
        this.locations[i][j] = code;
    }

    highlight(i, j, color) {
        this.drawing.ctx.save();
        this.drawing.ctx.beginPath();
        this.drawing.ctx.strokeStyle = color;
        this.drawing.ctx.lineWidth = 3.0;
        this.drawing.ctx.arc(this.x(i, j), this.y(i, j), this.drawing.unit * 0.4, 0, 2 * Math.PI);
        this.drawing.ctx.stroke();
        this.drawing.ctx.restore();
    }

    movePiece(i_from, j_from, i_to, j_to) {
        this.locations[i_to][j_to] = this.locations[i_from][j_from];
        this.locations[i_from][j_from] = null;
        this.game.hops += 1;
        this.game.didSingleHop = Math.abs(i_to-i_from) <= 1 && Math.abs(j_to-j_from) <= 1;
        if (this.drawing.enabled) {
            this.drawBoard();
            this.drawAllPieces();
        }
    }

    initLocations() {
        const width = this.width;
        const locations = [];
        for (let i = 0; i < width; i++) {
            const line = [];
            for (let j = 0; j < width; j++) {
                const color = this.nameFromCode(this.board[i][j]);
                if (this.player(color)) {
                    line.push(this.board[i][j]);
                } else {
                    line.push(null);
                }
            }
            locations.push(line);
        }
        this.locations = locations;
    }

    addPlayer(username, code) {
        this.game.players.push(new Player(username, code));
    }

    addRule(rule) {
        rule.check = rule.check.bind(this);
        this.game.rules.push(rule);
    }

    playerIdx(color) {
        for (let p = 0; p < this.game.players.length; p++) {
            if (this.game.players[p].color === color) {
                return p;
            }
        }
        return -1;
    }

    player(color) {
        const idx = this.playerIdx(color);
        if (idx !== -1) {
            return this.game.players[this.playerIdx(color)];
        }
        return undefined;
    }

    setCurrentPlayer(code) {
        this.game.currentPlayer = this.player(code);
    }
}
