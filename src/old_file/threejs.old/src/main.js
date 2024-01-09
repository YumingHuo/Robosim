import { io } from "socket.io-client";
import * as THREE from "three";
//import Orbit Controls
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";

//1. build scene
const scene = new THREE.Scene();

//2.build camara (perspective)
const camera = new THREE.OrthographicCamera(-2, 2, 2, -2, 1, 1000);
camera.position.set(0, 10, 0);
scene.add(camera);

//3. Initialize the renderer
const renderer = new THREE.WebGLRenderer();
renderer.setSize(1000, 1000);

//4. Add webgl rendered canvas content to body
document.body.appendChild(renderer.domElement);

//5. View 3d objects using the controller
new OrbitControls(camera, renderer.domElement);

//6. Add axis helper
const axesHelper = new THREE.AxesHelper(5);
scene.add(axesHelper);

//7. Add gridhelper
const size = 10;
const divisions = 10;
const gridHelper0 = new THREE.GridHelper(size, divisions);
gridHelper0.position.set(0, -0.5, 0);
scene.add(gridHelper0);


const box_geometry = new THREE.BoxGeometry(1, 1, 1);
const box_material = new THREE.MeshMatcapMaterial({ color: 0xffff00 });
function add_boxes(boxes) {
  let box_models = [];
  for (const [_, x, y] of boxes) {
    const box_model = new THREE.Mesh(box_geometry, box_material);
    box_model.position.set(x, 0, y);
    box_models.push(box_model);
    scene.add(box_model);
  }

  return box_models;
}

function remove_boxes(box_models) {
  for (const box_model of box_models) {
    scene.remove(box_model);
  }
}

let box_models = [];
function update_state(boxes) {
  remove_boxes(box_models);
  box_models = add_boxes(boxes);
}

const socket = io("http://localhost:4000");
socket.emit("subscribe");
socket.on("state", update_state);

//8. Start the main render loop
function render() {
  renderer.render(scene, camera);
  //Request the rendering of the next frame
  requestAnimationFrame(render);
}
render();
