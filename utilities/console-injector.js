{
  const head = document.getElementsByTagName("head")[0];
  const style = document.createElement("link");
  style.rel = "stylesheet";
  style.href = "http://127.0.0.1:5000/static/style.css";

  const socketio = document.createElement("script");
  socketio.type = "text/javascript";
  socketio.async = true;
  socketio.src = "https://cdn.socket.io/socket.io-3.0.5.min.js";
  socketio.onload = () => {
    const worker = document.createElement("script");
    worker.async = true;
    worker.type = "text/javascript";
    worker.src = "http://127.0.0.1:5000/static/worker.js";

    head.appendChild(worker);
  };

  head.appendChild(style);
  head.appendChild(socketio);
}
