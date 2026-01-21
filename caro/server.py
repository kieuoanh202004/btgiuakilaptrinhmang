import socket
import threading
import json

HOST = '0.0.0.0'  # Cho phép kết nối từ ngoài (LAN)
PORT = 5555
BUFFER_SIZE = 4096

clients = []
rooms = {}
room_counter = 0

def create_board():
    return [[' ' for _ in range(15)] for _ in range(15)]

def check_win(board, row, col, symbol):
    directions = [(0,1), (1,0), (1,1), (1,-1)]
    for dr, dc in directions:
        count = 1
        # chiều thuận
        r, c = row + dr, col + dc
        while 0 <= r < 15 and 0 <= c < 15 and board[r][c] == symbol:
            count += 1
            r += dr
            c += dc
        # chiều ngược
        r, c = row - dr, col - dc
        while 0 <= r < 15 and 0 <= c < 15 and board[r][c] == symbol:
            count += 1
            r -= dr
            c -= dc
        if count >= 5:
            return True
    return False

def handle_client(conn, addr):
    print(f"New connection: {addr}")
    conn.send("WELCOME".encode())

    try:
        while True:
            data = conn.recv(BUFFER_SIZE).decode().strip()
            if not data:
                break

            msg = json.loads(data)

            if msg['action'] == 'join_queue':
                if len(clients) == 0:
                    clients.append((conn, addr))
                    conn.send(json.dumps({"status": "waiting"}).encode())
                else:
                    # Ghép đôi
                    global room_counter
                    opponent_conn, opponent_addr = clients.pop(0)
                    room_counter += 1
                    room_id = room_counter

                    board = create_board()

                    rooms[room_id] = {
                        'player1': conn,
                        'player2': opponent_conn,
                        'board': board,
                        'turn': 'X',           # X đi trước
                        'symbols': {conn: 'X', opponent_conn: 'O'}
                    }

                    # Thông báo cho cả hai
                    msg_start = {
                        "status": "start",
                        "room_id": room_id,
                        "symbol": "X",
                        "your_turn": True
                    }
                    conn.send(json.dumps(msg_start).encode())

                    msg_start_op = {
                        "status": "start",
                        "room_id": room_id,
                        "symbol": "O",
                        "your_turn": False
                    }
                    opponent_conn.send(json.dumps(msg_start_op).encode())

            elif msg['action'] == 'move':
                room_id = msg['room_id']
                r, c = msg['row'], msg['col']

                if room_id not in rooms:
                    continue

                room = rooms[room_id]
                if room['turn'] != room['symbols'][conn]:
                    conn.send(json.dumps({"status": "not_your_turn"}).encode())
                    continue

                if room['board'][r][c] != ' ':
                    conn.send(json.dumps({"status": "invalid"}).encode())
                    continue

                symbol = room['symbols'][conn]
                room['board'][r][c] = symbol
                room['turn'] = 'O' if symbol == 'X' else 'X'

                # Gửi lại trạng thái cho cả hai người chơi
                state = {
                    "status": "update",
                    "board": room['board'],
                    "turn": room['turn']
                }

                room['player1'].send(json.dumps(state).encode())
                room['player2'].send(json.dumps(state).encode())

                # Kiểm tra thắng
                if check_win(room['board'], r, c, symbol):
                    win_msg = {"status": "win", "winner": symbol}
                    room['player1'].send(json.dumps(win_msg).encode())
                    room['player2'].send(json.dumps(win_msg).encode())
                    del rooms[room_id]
                    break

                # Hòa (đầy bàn cờ - đơn giản hóa)
                if all(cell != ' ' for row in room['board'] for cell in row):
                    draw_msg = {"status": "draw"}
                    room['player1'].send(json.dumps(draw_msg).encode())
                    room['player2'].send(json.dumps(draw_msg).encode())
                    del rooms[room_id]
                    break

    except Exception as e:
        print(f"Error with {addr}: {e}")
    finally:
        if conn in clients:
            clients.remove((conn, addr))
        conn.close()
        print(f"Disconnected: {addr}")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"Server listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    main()