"use strict";

{
  (function () {
    const ui = document.createElement("div");
    ui.id = "autolike-controls";
    ui.innerHTML = `
      <div class="row">
        <label for="probability">∄</label>
        <meter id="probability" min="0" low="30" high="70" max="100" optimum="100" value="50"></meter>
        <label for="probability">∀</label>
      </div>

      <div class="row">
        <input type="checkbox" id="autolike">
        <label for="autolike">Auto like</label>
      </div>

      <div class="row">
        <button id="dislike" title="Dislike">⊖</button>
        <button id="like" title="Like">⊕</button>
      </div>

      <div class="row">
        <div id="message">&hellip;</message>
      </div>
  	`;

    const body = document.getElementsByTagName("body")[0];
    body.appendChild(ui);
  })();

  const context = {
    recognize: false,
    selectors: {},
    autoskip: [],
    autowait: [],
  };
  const probability = document.getElementById("probability");
  const autolike = document.getElementById("autolike");
  const like = document.getElementById("like");
  const dislike = document.getElementById("dislike");
  const message = document.getElementById("message");
  const uri = "http://127.0.0.1:5000";
  const socket = io.connect(uri);

  function execute(selectors, callback) {
    for (const selector of selectors) {
      for (const element of document.querySelectorAll(selector)) {
        callback(element);

        break;
      }
    }
  }

  function update() {
    let found = false;
    let wait = false;

    execute(context.autoskip, (element) => {
      element.click();
      found = true;
    });
    execute(context.autowait, () => {
      wait = true;
    });

    if (found) {
      message.innerText = "Auto skip";

      setTimeout(update, 500);
    } else if (wait) {
      message.innerText = "Waiting...";

      setTimeout(update, 5 * 60);
    } else if (context.recognize) {
      context.recognize = false;
      socket.emit("recognize", {
        domain: document.domain,
        autolike: autolike.checked,
      });
    }
  }

  socket.on("connect", async () => {
    socket.emit("initialize", { domain: document.domain });
  });

  socket.on("start", async () => {
    context.recognize = true;
    setTimeout(update, 500);
  });

  socket.on("set", async (data, callback) => {
    message.innerText = "set(`" + data.name + "`, `" + data.value + "`)";
    context.selectors[data.name] = data.value;

    callback();
  });

  socket.on("autoskip", async (data, callback) => {
    message.innerText = "autoskip(`" + data.value + "`)";
    context.autoskip.push(data.value);

    callback();
  });

  socket.on("autowait", async (data, callback) => {
    message.innerText = "autowait(`" + data.value + "`)";
    context.autowait.push(data.value);

    callback();
  });

  socket.on("count", async (data, callback) => {
    message.innerText = "count(`" + data.name + "`)";

    const selector = context.selectors[data.name];
    const elements = document.querySelectorAll(selector);

    callback(elements.length);
  });

  socket.on("text", async (data, callback) => {
    message.innerText = "text(`" + data.name + "`)";

    const selector = context.selectors[data.name];
    const element = document.querySelector(selector);

    if (element != null) {
      callback(element.innerText);
    } else {
      callback("");
    }
  });

  socket.on("attribute", async (data, callback) => {
    message.innerText =
      "attribute(`" + data.name + "`, `" + data.attribute + "`)";

    const selector = context.selectors[data.name];
    const element = document.querySelector(selector);

    if (element != null) {
      callback(element[data.attribute]);
    } else {
      callback(null);
    }
  });

  socket.on("click", async (data, callback) => {
    message.innerText = "click(`" + data.name + "`)";

    const selector = context.selectors[data.name];
    const element = document.querySelector(selector);

    if (element != null) {
      element.click();

      callback(true);
    } else {
      callback(false);
    }
  });

  socket.on("prediction", async (data) => {
    probability.innerText = 100.0 * data.value;
  });

  socket.on("message", async (data) => {
    message.innerText = data.message;
  });

  like.addEventListener("click", (event) => {
    socket.emit("like", {});
  });

  dislike.addEventListener("click", (event) => {
    socket.emit("dislike", {});
  });
}
