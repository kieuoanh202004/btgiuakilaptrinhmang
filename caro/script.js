const statusEl = document.getElementById('status');
const joinBtn = document.getElementById('joinBtn');
const quitBtn = document.getElementById('quitBtn');
const boardEl = document.getElementById('board');
const mySymbolEl = document.getElementById('mySymbol');
const turnInfoEl = document.getElementById('turnInfo');
const infoEl = document.getElementById('info');

const defaultHeader = document.getElementById('defaultHeader');
const playersHeader = document.getElementById('playersHeader');
const enemySymbolEl = document.getElementById('enemySymbol');

let ws = null;
let roomId = null;
let mySymbol = null;
let myTurn = false;

/* ======================
   TẠO BÀN CỜ (GIỮ NGUYÊN)
====================== */
const createBoard = () => {
    boardEl.innerHTML = '';
    for (let i = 0; i < 15; i++) {
        for (let j = 0; j < 15; j++) {
            const cell = document.createElement('div');
            cell.classList.add('cell');
            cell.dataset.row = i;
            cell.dataset.col = j;
            cell.onclick = () => makeMove(i, j);
            boardEl.appendChild(cell);
        }
    }
};

/* ======================
   KẾT NỐI SERVER (GIỮ LOGIC)
====================== */
const connect = () => {
    ws = new WebSocket('ws://127.0.0.1:8001');

    ws.onopen = () => {
        statusEl.textContent = 'Đã kết nối! Nhấn "Tìm trận ngay" để chơi.';
        statusEl.style.color = '#fff';
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        console.log('Server:', msg);

        if (msg.status === 'waiting') {
            statusEl.textContent = 'Đang tìm đối thủ...';
        } else if (msg.status === 'start') {
            roomId = msg.room_id;
            mySymbol = msg.symbol;
            myTurn = msg.your_turn;

            mySymbolEl.textContent = mySymbol;
            enemySymbolEl.textContent = mySymbol === 'X' ? 'O' : 'X';

            turnInfoEl.textContent = myTurn ? 'Đến lượt bạn' : 'Đợi đối thủ';
            statusEl.textContent = '🔥 Trận đấu bắt đầu!';

            // UI theo yêu cầu
            boardEl.classList.remove('hidden');
            defaultHeader.classList.add('hidden');
            playersHeader.classList.remove('hidden');
            infoEl.style.display = 'none';

            createBoard();
        } else if (msg.status === 'update') {
            const cells = boardEl.querySelectorAll('.cell');

            msg.board.forEach((rowArr, rowIndex) => {
                rowArr.forEach((val, colIndex) => {
                    const index = rowIndex * 15 + colIndex;
                    const cell = cells[index];

                    cell.textContent = val;
                    cell.classList.remove('x', 'o');
                    if (val === 'X') cell.classList.add('x');
                    if (val === 'O') cell.classList.add('o');
                });
            });

            // 🔥 GIỮ NGUYÊN LOGIC GỐC
            myTurn = msg.turn === mySymbol;
            turnInfoEl.textContent = myTurn ? 'Đến lượt bạn' : 'Đợi đối thủ';
        } else if (msg.status === 'win') {
            alert(msg.winner === mySymbol
                ? 'CHÚC MỪNG: BẠN THẮNG!'
                : 'RẤT TIẾC: BẠN THUA!');
            resetGame();
        } else if (msg.status === 'draw') {
            alert('Hòa!');
            resetGame();
        }
    };

    ws.onclose = () => {
        statusEl.textContent = 'Mất kết nối server...';
        statusEl.style.color = 'red';
    };
};

/* ======================
   TÌM TRẬN
====================== */
const joinQueue = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({action: 'join_queue'}));
    }
};

/* ======================
   ĐÁNH CỜ (GIỮ NGUYÊN)
====================== */
const makeMove = (row, col) => {
    if (!myTurn) {
        console.log('Không phải lượt của bạn!');
        return;
    }
    if (!roomId || !ws) return;

    const cells = boardEl.querySelectorAll('.cell');
    const cell = cells[row * 15 + col];
    if (cell.textContent.trim() !== '') return;

    ws.send(JSON.stringify({
        action: 'move',
        room_id: roomId,
        row,
        col
    }));
};

/* ======================
   RESET
====================== */
const resetGame = () => {
    roomId = null;
    mySymbol = null;
    myTurn = false;

    mySymbolEl.textContent = '-';
    turnInfoEl.textContent = 'Chưa bắt đầu';
    statusEl.textContent = 'Nhấn "Tìm trận ngay" để chơi lại';

    boardEl.classList.add('hidden');
    playersHeader.classList.add('hidden');
    defaultHeader.classList.remove('hidden');
    infoEl.style.display = 'block';
};

/* ======================
   EVENT
====================== */
joinBtn.addEventListener('click', joinQueue);
quitBtn.addEventListener('click', () => {
    if (ws) ws.close();
    resetGame();
});

/* ======================
   START
====================== */
connect();
