const statusEl = document.getElementById('status');
const joinBtn = document.getElementById('joinBtn');
const quitBtn = document.getElementById('quitBtn');
const boardEl = document.getElementById('board');
const mySymbolEl = document.getElementById('mySymbol');
const turnInfoEl = document.getElementById('turnInfo');

let ws = null;
let roomId = null;
let mySymbol = null;
let myTurn = false;

// Hàm tạo bàn cờ trống
const createBoard = () => {
  boardEl.innerHTML = '';
  for (let i = 0; i < 15; i++) {
    for (let j = 0; j < 15; j++) {
      const cell = document.createElement('div');
      cell.classList.add('cell');
      cell.dataset.row = i;
      cell.dataset.col = j;
      // Gắn sự kiện click
      cell.onclick = () => makeMove(i, j);
      boardEl.appendChild(cell);
    }
  }
};

const connect = () => {
  // Kết nối đến cổng 8001 của caro_server_web.py
  ws = new WebSocket('ws://127.0.0.1:8001');

  ws.onopen = () => {
    statusEl.textContent = 'Đã kết nối! Nhấn "Tìm trận ngay" để chơi.';
    statusEl.style.color = '#fff';
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    console.log("Nhận tin nhắn từ server:", msg); // Để debug

    if (msg.status === 'waiting') {
      statusEl.textContent = 'Đang tìm đối thủ...';
    }

    else if (msg.status === 'start') {
      roomId = msg.room_id;
      mySymbol = msg.symbol;
      myTurn = msg.your_turn;

      mySymbolEl.textContent = mySymbol;
      mySymbolEl.style.color = (mySymbol === 'X' ? '#ff4d4d' : '#4d79ff');

      turnInfoEl.textContent = myTurn ? 'Đến lượt bạn' : 'Đợi đối thủ';
      statusEl.textContent = 'Trận đấu bắt đầu!';
      createBoard();
    }

    else if (msg.status === 'update') {
      const cells = boardEl.querySelectorAll('.cell');
      msg.board.forEach((rowArr, rowIndex) => {
        rowArr.forEach((val, colIndex) => {
          const index = rowIndex * 15 + colIndex;
          const cell = cells[index];

          cell.textContent = val;
          // Quan trọng: Xóa class cũ để hiển thị đúng màu quân O
          cell.classList.remove('x', 'o');
          if (val === 'X') cell.classList.add('x');
          if (val === 'O') cell.classList.add('o');
        });
      });

      myTurn = (msg.turn === mySymbol);
      turnInfoEl.textContent = myTurn ? 'Đến lượt bạn' : 'Đợi đối thủ';
    }

    else if (msg.status === 'win') {
      const result = msg.winner === mySymbol ? 'CHÚC MỪNG: BẠN THẮNG!' : 'RẤT TIẾC: BẠN THUA!';
      alert(result);
      resetGame();
    }

    else if (msg.status === 'draw') {
      alert('Hòa!');
      resetGame();
    }
  };

  ws.onclose = () => {
    statusEl.textContent = 'Mất kết nối server...';
    statusEl.style.color = 'red';
  };
};

const joinQueue = () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'join_queue' }));
  } else {
    alert("Chưa kết nối được server. Vui lòng kiểm tra Terminal!");
  }
};

const makeMove = (row, col) => {
  // Kiểm tra điều kiện trước khi đánh
  if (!myTurn) {
    console.log("Không phải lượt của bạn!");
    return;
  }
  if (!roomId || !ws) return;

  const cells = boardEl.querySelectorAll('.cell');
  const cell = cells[row * 15 + col];

  if (cell.textContent.trim() !== '') return;

  // Gửi nước đi tới server
  ws.send(JSON.stringify({
    action: 'move',
    room_id: roomId,
    row: row,
    col: col
  }));
};

const resetGame = () => {
  roomId = null;
  mySymbol = null;
  myTurn = false;
  mySymbolEl.textContent = '-';
  turnInfoEl.textContent = 'Chưa bắt đầu';
  statusEl.textContent = 'Nhấn "Tìm trận ngay" để chơi lại';
  createBoard();
};

joinBtn.addEventListener('click', joinQueue);
quitBtn.addEventListener('click', () => {
  if (ws) ws.close();
  alert("Cảm ơn bạn đã chơi!");
});

// Khởi chạy
connect();
createBoard();