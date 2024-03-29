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
        Age: <span id="age">&mdash;</span>,
        Gender: <span id="gender">&mdash;</span>
      </div>

      <div class="row">
        Race: <span id="race">&mdash;</span>
      </div>

      <div class="row">
        <input type="checkbox" id="autolike">
        <label for="autolike">Auto like</label>
      </div>

      <div class="row">
        <button id="dislike" title="Dislike">⊖</button>
        <button id="analyze" title="Analyze">≋</button>
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
  const age = document.getElementById("age");
  const gender = document.getElementById("gender");
  const race = document.getElementById("race");
  const autolike = document.getElementById("autolike");
  const like = document.getElementById("like");
  const analyze = document.getElementById("analyze");
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
      message.innerText = "auto skip";

      setTimeout(update, 500);
    } else if (wait) {
      message.innerText = "waiting...";

      setTimeout(update, 10 * 60);
    } else if (context.recognize) {
      context.recognize = false;
      socket.emit("recognize", { domain: document.domain });
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

    await callback();
  });

  socket.on("autoskip", async (data, callback) => {
    message.innerText = "autoskip(`" + data.value + "`)";
    context.autoskip.push(data.value);

    await callback();
  });

  socket.on("autowait", async (data, callback) => {
    message.innerText = "autowait(`" + data.value + "`)";
    context.autowait.push(data.value);

    await callback();
  });

  socket.on("count", async (data, callback) => {
    message.innerText = "count(`" + data.name + "`)";

    const selector = context.selectors[data.name];
    const elements = document.querySelectorAll(selector);

    await callback(elements.length);
  });

  socket.on("text", async (data, callback) => {
    message.innerText = "text(`" + data.name + "`)";

    const selector = context.selectors[data.name];
    const element = document.querySelector(selector);

    if (element != null) {
      await callback(element.innerText);
    } else {
      await callback("");
    }
  });

  socket.on("attribute", async (data, callback) => {
    message.innerText =
      "attribute(`" + data.name + "`, `" + data.attribute + "`)";

    const selector = context.selectors[data.name];
    const element = document.querySelector(selector);

    if (element != null) {
      await callback(element[data.attribute]);
    } else {
      await callback(null);
    }
  });

  socket.on("attributes", async (data, callback) => {
    message.innerText =
      "attributes(`" + data.name + "`, `" + data.attribute + "`)";

    const selector = context.selectors[data.name];
    const elements = document.querySelectorAll(selector);
    const result = Array.from(elements, (element) => element[data.attribute]);

    await callback(result);
  });

  socket.on("click", async (data, callback) => {
    message.innerText = "click(`" + data.name + "`)";

    const selector = context.selectors[data.name];
    const element = document.querySelector(selector);

    if (element != null) {
      element.dispatchEvent(new Event("click", { bubbles: true }));

      await callback(true);
    } else {
      await callback(false);
    }
  });

  socket.on("prediction", async (data) => {
    probability.value = 100.0 * data.probability;
    age.innerText = data.age || "\u2014";

    if (data.gender == null) {
      gender.innerText = "\u2014";
    } else if (data.gender == "woman") {
      gender.innerText = "\u2640";
    } else if (data.gender == "man") {
      gender.innerText = "\u2642";
    } else {
      gender.innerText = "\u2014";
    }

    if (data.race == null) {
      race.innerText = "\u2014";
    } else {
      race.innerText = data.race;
    }
  });

  socket.on("message", async (data) => {
    message.innerText = data.message;
  });

  like.addEventListener("click", (event) => {
    socket.emit("like", {});
  });

  analyze.addEventListener("click", (event) => {
    context.recognize = true;
    setTimeout(update, 500);
  });

  dislike.addEventListener("click", (event) => {
    socket.emit("dislike", {});
  });
}
