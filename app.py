import importlib

app_module = importlib.import_module("ãpp")
app = app_module.app
socketio = app_module.socketio


if __name__ == "__main__":
    socketio.run(app, debug=True)
