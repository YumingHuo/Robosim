import { io } from "https://cdn.socket.io/4.4.1/socket.io.esm.min.js";

const NO_ACCESS_MESSAGE =
  "Invalid, You don't have access, please click Acquire Access button.";

// show return output in console
const ack = function (r) {
  add_log_message(r);
};

const selectedBox = document.getElementById("selectedBox");
let currentSelection = -1;
selectedBox.onchange = function () {
  currentSelection = selectedBox.selectedIndex;
};

function state_data(state) {
  data = state;
}

function box_id_check(new_box_id) {
  for (var i = 0; i < selectedBox.length; i++) {
    if (new_box_id == selectedBox[i].value) {
      return true;
    }
  }
  return false;
}

function updated_state(state) {
  // remove the old
  for (let i = selectedBox.options.length - 1; i >= 0; i--) {
    selectedBox.remove(i);
  }
  // add the new
  for (let i = 0; i < state.length; i++) {
    let new_option = document.createElement("option");
    new_option.text = state[i][0].toString();
    selectedBox.add(new_option);
  }

  if (currentSelection === -1 && selectedBox.options.length > 0) {
    currentSelection = 0;
  }
  selectedBox.selectedIndex = currentSelection;
}

function kickOutLogin() {
  if (isConnected && !access && !release_checker) {
    add_log_message("Invalid, You have no exclusive access to release");
  }
  if (isConnected && !access && release_checker) {
    add_log_message("Invalid, You've already released exclusive access");
  }
  if (isConnected && access && !release_checker) {
    socket.emit("release_access");
    access = false;
    release_checker = true;
    document.getElementById('status').classList.remove('green');
    document.getElementById('status').classList.remove('yellow');
    document.getElementById('status').classList.add('red');
    add_log_message("Invalid, administrator has forced login");
  }
}

function selected_box_id() {
  const index = selectedBox.selectedIndex;
  if (index != undefined) {
    return parseInt(selectedBox[index].value);
  }
  return undefined;
}

function get_positive_integer(prompt_message, error_message) {
  let value = -1;
  do {
    let input = prompt(prompt_message);
    if (input === null) return null;
    value = parseInt(input);
    if (isNaN(value)) {
      value = -1;
      alert(error_message);
    } else if (value < 0) {
      alert(error_message);
    }
  } while (value < 0);

  return value;
}

function if_valid(f, error_message) {
  if (isConnected && access) {
    f();
  } else {
    add_log_message(error_message);
  }
}

document.getElementById("add_box").onclick = () =>
  if_valid(function () {
    let negative_error = "Please enter a non-negative number";
    let boxId = -1;
    do {
      let input = prompt("box id (must be a non-negative number)");
      if (input === null) return;
      boxId = parseInt(input);
      if (isNaN(boxId)) {
        boxId = -1;
        alert(negative_error);
      } else if (box_id_check(boxId) == true) {
        boxId = -1;
        alert("This box_id has already been added in the warehouse");
      } else if (boxId < 0) {
        alert(negative_error);
      }
    } while (boxId < 0);

    let x = get_positive_integer(
      "x coordinate (must be a non-negative number)",
      negative_error
    );
    if (x === null) return;

    let y = get_positive_integer(
      "y coordinate (must be a non-negative number)",
      negative_error
    );
    if (y === null) return;

    let z = get_positive_integer(
      "z coordinate (must be a non-negative number)",
      negative_error
    );
    if (z === null) return;

    socket.emit(
      "add_box",
      {
        box_id: boxId,
        x: x,
        y: y,
        z: z,
      },
      ack
    );
  }, NO_ACCESS_MESSAGE);

document.getElementById("remove_box").onclick = () =>
  if_valid(function () {
    const boxId = selected_box_id();
    socket.emit("remove_box", boxId, ack);
    currentSelection = -1;
  }, NO_ACCESS_MESSAGE);

document.getElementById("upload_CSV").onclick = () =>
  if_valid(function () {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".csv";
    input.multiple = false;

    input.onchange = function (event) {
      const file = event.target.files[0];
      const reader = new FileReader();

      reader.onload = function (event) {
        const fileContent = event.target.result;

        const data = parseCSV(fileContent);

        const dataString = data.map((row) => row.join(",")).join("\n");

        socket.emit("csv_upload", dataString, ack);
      };

      reader.readAsText(file);
    };

    input.click();
  }, NO_ACCESS_MESSAGE);

function parseCSV(csvString) {
  const rows = csvString.trim().split("\n");
  return rows.map((row) => row.trim().split(","));
}

function assign_move(direction) {
  document.getElementById(direction).onclick = function () {
    emit_direction(direction);
  };
}

function assign_camera_preset(preset) {
  document.getElementById("camera_preset_" + preset).onclick = function () {
    socket.emit("set_camera_preset", preset, ack);
  };
}

function emit_direction(direction) {
  if_valid(function () {
    socket.emit(
      "move_box",
      {
        box_id: selected_box_id(),
        direction,
      },
      ack
    );
  }, NO_ACCESS_MESSAGE);
}

async function update_image() {
  if (isConnected) {
    let canvas = document.getElementById("image");
    let ctx = canvas.getContext("bitmaprenderer");

    let image_response = await fetch("/image", { method: "GET" });
    let blob = await image_response.blob();

    let reader = new FileReader();
    reader.onload = function (e) {
      let image = new Image();
      image.onload = async function () {
        let image_bitmap = await createImageBitmap(image);
        ctx.transferFromImageBitmap(image_bitmap);
      };
      image.src = e.target.result;
    };

    reader.readAsDataURL(blob);
  }
}

// global variable to keep track of connection status
let isConnected;
let socket;
let data;
function main() {
  // create socket connection at 4000 port on same host
  socket = io(window.location.host + ":4000");

  // maintain the isConnected Global variable
  isConnected = false;
  socket.on("connect", () => {
    add_log_message("connected to server");
    socket.emit("subscribe_updates");
    socket.emit("get_state", updated_state);
    isConnected = true;
  });
  socket.on("disconnect", () => {
    isConnected = false;
    document.getElementById('status').classList.remove('green');
    document.getElementById('status').classList.add('red');
    add_log_message("disconnected from server");
  });
  socket.on("state", updated_state);
  socket.on("state", state_data);
  socket.on("kick_out_login", kickOutLogin);

  // assign callbacks on the movement buttons
  assign_move("north");
  assign_move("south");
  assign_move("east");
  assign_move("west");
  assign_move("up");
  assign_move("down");

  // assign callbacks on the camera preset buttons
  assign_camera_preset("front");
  assign_camera_preset("back");
  assign_camera_preset("top");

  // start image updating Interval and maintain on fps input change
  setInterval(update_image, 100);
}

main();

let lineNumber = 1;
function add_log_message(message) {
  if (message === undefined) {
    return;
  }

  let logger = document.getElementById("logger");
  let colour = message.includes("Invalid") ? "color:red;" : "color:green";
  logger.innerHTML += `<span style = "${colour}">${lineNumber}. ${message}</span><br>`;

  lineNumber++;

  let logWindow = document.getElementById("logWindow");
  logWindow.scrollTop = logWindow.scrollHeight;
}

const domId1 = ["logWindow", "body", "img"];
const domId2 = [
  "add_box",
  "north",
  "south",
  "east",
  "west",
  "up",
  "down",
  "remove_box",
  "camera_preset_front",
  "camera_preset_top",
  "camera_preset_back",
  "upload_CSV",
  "download_CSV",
  "clear_all_boxes",
  "leaderboard",
  "access",
  "release",
];

function make_dark() {
  for (const domId of domId1) {
    let dom = document.getElementById(domId);
    dom.classList.remove(domId);
    dom.classList.add(`${domId}_dark`);
  }


  for (const domId of domId2) {
    let dom = document.getElementById(domId);
    dom.classList.remove("btn-main");
    dom.classList.add(`${domId}_dark`);
  }
  if (isConnected) {
    socket.emit("mode", "dark");
  }
}

function make_light() {
  for (const domId of domId1) {
    let dom = document.getElementById(domId);
    dom.classList.remove(`${domId}_dark`);
    dom.classList.add(domId);
  }

  for (const domId of domId2) {
    let dom = document.getElementById(domId);
    dom.classList.remove(`${domId}_dark`);
    dom.classList.add("btn-main");
  }

  if (isConnected) {
    socket.emit("mode", "light");
  }
}

document.getElementById("moon").onclick = make_dark;
document.getElementById("sun").onclick = make_light;

let title = "warehouse";
let head = ["box_id", "x", "y", "z", "10", "10", "10"];

function isMSbrowser() {
  const userAgent = window.navigator.userAgent;
  return (
    userAgent.indexOf("Edge") !== -1 || userAgent.indexOf("Trident") !== -1
  );
}

function format(data) {
  return String(data)
    .replace(/"/g, '""')
    .replace(/(^[\s\S]*$)/, '"$1"');
}

function saveCSV(title, head, data) {
  let wordSeparator = ",";
  let lineSeparator = "\n";

  let reTitle = title + ".csv";
  let headBOM = "\ufeff";
  let headStr = head
    ? head.map((item) => format(item)).join(wordSeparator) + lineSeparator
    : "";
  let dataStr = data
    ? data
      .map((row) => row.map((item) => format(item)).join(wordSeparator))
      .join(lineSeparator)
    : "";

  return isMSbrowser()
    ? new Promise((resolve) => {
      // Edge、IE11
      let blob = new Blob([headBOM + headStr + dataStr], {
        type: "text/plain;charset=utf-8",
      });
      window.navigator.msSaveBlob(blob, reTitle);
      resolve();
    })
    : new Promise((resolve) => {
      // Chrome、Firefox
      let a = document.createElement("a");
      a.href =
        "data:text/csv;charset=utf-8," +
        headBOM +
        encodeURIComponent(headStr + dataStr);
      a.download = reTitle;
      a.click();
      resolve();
    });
}

download_CSV.onclick = function downloadCSV() {
  if_valid(function () {
    saveCSV(title, head, data).then(() => {
      console.log("Download CSV file successfully");
    });
  }, NO_ACCESS_MESSAGE);
};

document.getElementById("clear_all_boxes").onclick = function () {
  if_valid(function () {
    socket.emit("clear_all_boxes", ack);
  }, NO_ACCESS_MESSAGE);
};

let access = false;
let release_checker = false;

document.getElementById("access").onclick = function () {
  if (isConnected && !access) {
    const username = window.prompt("Please Enter Username");
    const password = window.prompt("Please Enter Password");

    socket.emit("get_access", { username: username, password: password }, function (response) {
      if (typeof response === 'string') {
        add_log_message(response)
      } else {
        access = response;
        release_checker = false;
        if (response == 1) {
          document.getElementById('status').classList.remove('red');
          document.getElementById('status').classList.add('green');
          add_log_message("You now have exclusive access to the warehouse");
        } else if (response == 2) {
          document.getElementById('status').classList.remove('red');
          document.getElementById('status').classList.add('yellow');
          add_log_message("You now have exclusive access to the warehouse as administrator");
        } else {
          document.getElementById('status').classList.remove('green');
          document.getElementById('status').classList.add('red');
          add_log_message(
            "Invalid, another person is using the warehouse, please wait until they release it"
          );
        }
      }
    });
  } else {
    add_log_message("Invalid, you already have exclusive access");
  }
};


document.getElementById("release").onclick = function () {
  if (isConnected && !access && !release_checker) {
    add_log_message("Invalid, you have no exclusive access to release");
  }
  if (isConnected && !access && release_checker) {
    add_log_message("Invalid, you've already released exclusive access");
  }
  if (isConnected && access && !release_checker) {
    socket.emit("release_access");
    access = false;
    release_checker = true;
    document.getElementById('status').classList.remove('green');
    document.getElementById('status').classList.remove('yellow');
    document.getElementById('status').classList.add('red');
    add_log_message("You have now released your exclusive access to the warehouse");
  }
};
