# python
# File: `caro/ws_bridge.py`
import asyncio
import websockets
import logging

TCP_HOST = "127.0.0.1"
TCP_PORT = 5555           # existing game server port
WS_HOST = "127.0.0.1"
WS_PORT = 8001            # browser will connect here
BUFFER_SIZE = 4096

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

async def handle_ws(ws, path):
    logging.info("New WS client connected")
    try:
        reader, writer = await asyncio.open_connection(TCP_HOST, TCP_PORT)
    except Exception as e:
        logging.error(f"Cannot connect to TCP server {TCP_HOST}:{TCP_PORT}: {e}")
        await ws.close()
        return

    async def ws_to_tcp():
        try:
            async for msg in ws:
                # msg is a str (text) from browser; forward as bytes to TCP server
                if isinstance(msg, str):
                    writer.write(msg.encode())
                else:
                    writer.write(msg)
                await writer.drain()
        except (websockets.ConnectionClosed, asyncio.CancelledError):
            pass
        except Exception as e:
            logging.error(f"ws_to_tcp error: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def tcp_to_ws():
        try:
            while True:
                data = await reader.read(BUFFER_SIZE)
                if not data:
                    break
                # forward raw TCP payload as text to websocket client
                try:
                    text = data.decode()
                except Exception:
                    text = data.decode(errors="replace")
                await ws.send(text)
        except (websockets.ConnectionClosed, asyncio.CancelledError):
            pass
        except Exception as e:
            logging.error(f"tcp_to_ws error: {e}")
        finally:
            try:
                await ws.close()
            except Exception:
                pass

    task1 = asyncio.create_task(ws_to_tcp())
    task2 = asyncio.create_task(tcp_to_ws())

    done, pending = await asyncio.wait([task1, task2], return_when=asyncio.FIRST_COMPLETED)
    for t in pending:
        t.cancel()

    # ensure connections closed
    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass
    try:
        await ws.close()
    except Exception:
        pass
    logging.info("Bridge closed for a WS client")

async def main():
    server = await websockets.serve(handle_ws, WS_HOST, WS_PORT)
    logging.info(f"WebSocket bridge listening on ws://{WS_HOST}:{WS_PORT} -> TCP {TCP_HOST}:{TCP_PORT}")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bridge stopped by user")
