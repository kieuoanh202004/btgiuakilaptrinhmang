import asyncio
import json
import websockets

HOST = '0.0.0.0'
PORT = 8001

clients_queue = []
rooms = {}
room_counter = 0


def create_board():
    return [[' ' for _ in range(15)] for _ in range(15)]


def check_win(board, row, col, symbol):
    directions = [(0,1), (1,0), (1,1), (1,-1)]
    for dr, dc in directions:
        count = 1
        # hướng thuận
        r, c = row + dr, col + dc
        while 0 <= r < 15 and 0 <= c < 15 and board[r][c] == symbol:
            count += 1
            r += dr
            c += dc
        # hướng ngược
        r, c = row - dr, col - dc
        while 0 <= r < 15 and 0 <= c < 15 and board[r][c] == symbol:
            count += 1
            r -= dr
            c -= dc
        if count >= 5:
            return True
    return False


async def handle_client(websocket):
    global room_counter
    print(f"Người chơi kết nối: {websocket.remote_address}")

    try:
        async for message in websocket:
            data = json.loads(message)

            if data['action'] == 'join_queue':
                # Kiểm tra nếu người chơi đã trong hàng chờ thì không thêm nữa
                if websocket not in clients_queue:
                    if not clients_queue:
                        clients_queue.append(websocket)
                        await websocket.send(json.dumps({"status": "waiting"}))
                    else:
                        opponent = clients_queue.pop(0)
                        room_counter += 1
                        rid = room_counter
                        board = create_board()
                        rooms[rid] = {
                            'p1': websocket, 'p2': opponent,
                            'board': board, 'turn': 'X',
                            'sym': {websocket: 'X', opponent: 'O'}
                        }
                        # Gửi thông báo bắt đầu cho cả 2
                        await websocket.send(
                            json.dumps({"status": "start", "room_id": rid, "symbol": "X", "your_turn": True}))
                        await opponent.send(
                            json.dumps({"status": "start", "room_id": rid, "symbol": "O", "your_turn": False}))

            elif data['action'] == 'move':
                rid = data['room_id']
                if rid not in rooms: continue
                room = rooms[rid]

                # Kiểm tra đúng lượt
                if room['turn'] != room['sym'][websocket]:
                    await websocket.send(json.dumps({"status": "not_your_turn"}))
                    continue

                r, c = data['row'], data['col']
                if room['board'][r][c] == ' ':
                    symbol = room['sym'][websocket]
                    room['board'][r][c] = symbol
                    room['turn'] = 'O' if symbol == 'X' else 'X'

                    update = {"status": "update", "board": room['board'], "turn": room['turn']}
                    await room['p1'].send(json.dumps(update))
                    await room['p2'].send(json.dumps(update))

                    if check_win(room['board'], r, c, symbol):
                        win_msg = {"status": "win", "winner": symbol}
                        await room['p1'].send(json.dumps(win_msg))
                        await room['p2'].send(json.dumps(win_msg))
                        del rooms[rid]

    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        if websocket in clients_queue:
            clients_queue.remove(websocket)
        print("Một người chơi đã thoát.")


async def main():
    async with websockets.serve(handle_client, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())