# python
# File: `caro/client.py`
import tkinter as tk
from tkinter import messagebox
import socket
import threading
import json

class CaroClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Cờ Caro Online - Multiplayer")
        self.root.geometry("650x750")

        self.client = None
        self.room_id = None
        self.my_symbol = None
        self.my_turn = False
        self.buttons = [[None for _ in range(15)] for _ in range(15)]

        self.status_label = tk.Label(root, text="Đang kết nối...", font=("Arial", 14))
        self.status_label.pack(pady=10)

        self.connect_to_server()

        self.create_board()
        self.create_controls()

    def connect_to_server(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect(("127.0.0.1", 5555))  # Thay bằng IP server nếu chơi LAN
            threading.Thread(target=self.receive_messages, daemon=True).start()
            self.status_label.config(text="Đã kết nối! Nhấn 'Tìm trận' để chơi.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không kết nối được server: {e}")
            self.root.quit()

    def create_board(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        for i in range(15):
            for j in range(15):
                btn = tk.Button(frame, text=" ", font=("Arial", 16), width=2, height=1,
                                command=lambda r=i, c=j: self.make_move(r, c))
                btn.grid(row=i, column=j)
                self.buttons[i][j] = btn

    def create_controls(self):
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Tìm trận", font=("Arial", 12), command=self.join_queue).pack(side=tk.LEFT, padx=20)
        tk.Button(btn_frame, text="Thoát", font=("Arial", 12), command=self.quit_game).pack(side=tk.LEFT, padx=20)

    def join_queue(self):
        if self.client:
            msg = {"action": "join_queue"}
            try:
                self.client.send(json.dumps(msg).encode())
            except Exception:
                pass
            self.status_label.config(text="Đang tìm đối thủ...")

    def make_move(self, row, col):
        if not self.my_turn or self.room_id is None or self.buttons[row][col]["text"] != " ":
            return

        msg = {
            "action": "move",
            "room_id": self.room_id,
            "row": row,
            "col": col
        }
        try:
            self.client.send(json.dumps(msg).encode())
        except Exception:
            pass

    def receive_messages(self):
        while True:
            try:
                data = self.client.recv(4096)
                if not data:
                    break

                try:
                    text = data.decode().strip()
                except Exception:
                    # cannot decode, skip
                    continue

                if text == "":
                    continue

                # Try parse JSON; if it's not JSON (e.g. "WELCOME"), ignore
                try:
                    msg = json.loads(text)
                except (json.JSONDecodeError, ValueError):
                    # ignore non-JSON or partial data
                    continue

                if msg.get("status") == "waiting":
                    self.status_label.config(text="Đang chờ đối thủ...")

                elif msg.get("status") == "start":
                    self.room_id = msg["room_id"]
                    self.my_symbol = msg["symbol"]
                    self.my_turn = msg["your_turn"]
                    self.status_label.config(text=f"Bạn là {self.my_symbol} | {'Đến lượt bạn' if self.my_turn else 'Đợi đối thủ'}")

                elif msg.get("status") == "update":
                    board = msg["board"]
                    for i in range(15):
                        for j in range(15):
                            self.buttons[i][j]["text"] = board[i][j]
                            if board[i][j] == 'X':
                                self.buttons[i][j].config(fg="blue")
                            elif board[i][j] == 'O':
                                self.buttons[i][j].config(fg="red")
                    self.my_turn = (msg["turn"] == self.my_symbol)
                    self.status_label.config(text=f"{'Đến lượt bạn' if self.my_turn else 'Đợi đối thủ'}")

                elif msg.get("status") == "win":
                    winner = msg["winner"]
                    messagebox.showinfo("Kết thúc", f"{'Bạn thắng!' if winner == self.my_symbol else 'Bạn thua!'}")
                    self.reset_game()

                elif msg.get("status") == "draw":
                    messagebox.showinfo("Kết thúc", "Hòa!")
                    self.reset_game()

                elif msg.get("status") == "not_your_turn":
                    messagebox.showwarning("Thông báo", "Chưa đến lượt bạn!")

                elif msg.get("status") == "invalid":
                    messagebox.showwarning("Thông báo", "Ô đã được đánh!")

            except Exception as e:
                print("Lỗi nhận tin:", e)
                break

    def reset_game(self):
        for i in range(15):
            for j in range(15):
                self.buttons[i][j]["text"] = " "
                self.buttons[i][j].config(fg="black")
        self.room_id = None
        self.my_symbol = None
        self.my_turn = False
        self.status_label.config(text="Nhấn 'Tìm trận' để chơi lại")

    def quit_game(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = CaroClient(root)
    root.mainloop()
