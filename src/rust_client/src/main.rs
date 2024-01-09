use std::{
    cmp::{Ordering, Reverse},
    collections::HashMap,
    env::args,
    ops::Deref,
    sync::{Arc, Mutex},
    thread,
    time::{Duration, Instant},
};

use rust_socketio::ClientBuilder;
use rust_socketio::{client::Client, Payload};

use itertools::Itertools;

use priority_queue::PriorityQueue;

#[derive(Clone, Debug)]
struct Demand {
    box_id: usize,
    target_box_position: BoxPosition,
}

fn main() {
    let demands = args()
        .skip(1)
        .chunks(4)
        .into_iter()
        .map(|chunk| {
            let chunk = chunk.collect::<Vec<_>>();
            Demand {
                box_id: chunk[0].parse().unwrap(),
                target_box_position: BoxPosition {
                    x: chunk[1].parse().unwrap(),
                    y: chunk[2].parse().unwrap(),
                    z: chunk[3].parse().unwrap(),
                },
            }
        })
        .collect::<Vec<_>>();

    let connection = Connection::create("http://localhost:4000").expect("Can't connect to server!");

    loop {
        let mut storage = Storage::new(10, 10, 10);

        for (box_id, box_position) in connection.get_state() {
            storage.add_box_unchecked(box_id, box_position)
        }

        let all_moves = demands
            .iter()
            .map(|demand| {
                get_shortest_box_route(demand.box_id, demand.target_box_position, &storage)
            })
            .collect::<Vec<_>>();

        if all_moves
            .iter()
            .all(|x| x.as_ref().is_some_and(|x| x.is_empty()))
        {
            println!("All routes finished!");
            break;
        } else if all_moves.iter().all(|x| x.is_none()) {
            println!("Error no routes found for given demands!");
            break;
        }

        for first_box_move in all_moves
            .iter()
            .filter_map(|x| x.as_ref()?.first())
            .dedup()
        {
            println!("Move Sent to box {}!", first_box_move.box_id);
            connection.move_box(*first_box_move);
        }

        thread::sleep(Duration::from_secs(1));
    }
}

struct Connection {
    client: Client,
}

impl Connection {
    fn create(url: &str) -> Option<Connection> {
        let client = ClientBuilder::new(url).connect().ok()?;

        return Some(Connection { client });
    }

    fn move_box(&self, box_move: BoxMove) {
        println!("{}", box_move.to_json());
        self.client.emit("move_box", box_move.to_json()).unwrap();
    }

    fn get_state(&self) -> HashMap<BoxId, BoxPosition> {
        let string = self.get_state_string();
        let trimmed = string[3..(string.len() - 3)].to_string();
        let split = trimmed.split("],[");

        let result = split.map(|box_and_position| {
            let nums = box_and_position.split(",").collect::<Vec<_>>();
            (
                nums[0].parse().unwrap(),
                BoxPosition {
                    x: nums[1].parse().unwrap(),
                    y: nums[2].parse().unwrap(),
                    z: nums[3].parse().unwrap(),
                },
            )
        });
        return result.collect();
    }
    fn get_state_string(&self) -> String {
        let output = Arc::new(Mutex::new(None));
        let output2 = output.clone();

        let start = Instant::now();

        self.client
            .emit_with_ack(
                "get_state",
                "hi",
                Duration::from_secs(5),
                move |payload, _| match payload {
                    Payload::String(x) => {
                        *output2.lock().unwrap() = Some(x);
                    }
                    _ => panic!("not a string!"),
                },
            )
            .expect("emit failed");

        while start.elapsed() < Duration::from_secs(6) {
            if let Some(output) = output.lock().unwrap().deref() {
                return output.to_string();
            }

            thread::sleep(Duration::from_secs_f32(0.5));
            println!("waiting...")
        }

        panic!("no response to get_state")
    }
}

#[derive(Clone)]
struct Storage {
    width: usize,
    depth: usize,
    height: usize,
    box_positions: HashMap<BoxId, BoxPosition>,
    matrix: Vec<Vec<Vec<MatrixPosition>>>,
}

#[derive(Debug, Copy, Clone, PartialEq, Eq)]
struct BoxMove {
    box_id: BoxId,
    source_box_position: BoxPosition,
    destination_box_position: BoxPosition,
}

impl BoxMove {
    fn direction(&self) -> String {
        let s = self.source_box_position.as_tuple_signed();
        let d = self.destination_box_position.as_tuple_signed();
        let offset = (d.0 - s.0, d.1 - s.1, d.2 - s.2);

        match offset {
            (0, 0, 1) => "up",
            (0, 0, -1) => "down",
            (0, 1, 0) => "north",
            (0, -1, 0) => "south",
            (1, 0, 0) => "east",
            (-1, 0, 0) => "west",
            _ => panic!("unknown offset {offset:#?}"),
        }
        .to_string()
    }
    fn simplify(&self) -> Vec<BoxMove> {
        let z_same = self.source_box_position.z == self.destination_box_position.z;

        if z_same {
            return Vec::from([*self]);
        } else {
            let mid_box_position = BoxPosition {
                x: self.source_box_position.x,
                y: self.source_box_position.y,
                z: self.destination_box_position.z,
            };

            return Vec::from([
                BoxMove {
                    box_id: self.box_id,
                    source_box_position: self.source_box_position,
                    destination_box_position: mid_box_position,
                },
                BoxMove {
                    box_id: self.box_id,
                    source_box_position: mid_box_position,
                    destination_box_position: self.destination_box_position,
                },
            ]);
        }
    }

    fn to_json(&self) -> String {
        format!(
            "{{ \"box_id\": {}, \"direction\": \"{}\" }}",
            self.box_id,
            self.direction()
        )
    }
}

#[derive(Debug, Copy, Clone, PartialEq, Eq, Hash)]
struct BoxPosition {
    x: usize,
    y: usize,
    z: usize,
}

impl BoxPosition {
    //fn as_tuple_unsigned(&self) -> (usize, usize, usize) {
    //(self.x, self.y, self.z)
    //}

    fn as_tuple_signed(&self) -> (i8, i8, i8) {
        (self.x as i8, self.y as i8, self.z as i8)
    }
}

type BoxId = usize;

#[derive(Copy, Clone)]
enum MatrixPosition {
    Occupied(BoxId),
    NotOccupied,
    Blocked,
}

impl MatrixPosition {
    fn is_occupied(&self) -> bool {
        match self {
            MatrixPosition::Occupied(_) => true,
            _ => false,
        }
    }
    fn is_blocked(&self) -> bool {
        match self {
            MatrixPosition::Blocked => true,
            _ => false,
        }
    }

    fn box_id(&self) -> Option<BoxId> {
        match self {
            MatrixPosition::Occupied(box_id) => Some(*box_id),
            _ => None,
        }
    }
}

#[derive(Debug, Copy, Clone, PartialEq, Eq)]
struct Label {
    impeded_moves: u128,
    non_impeded_moves: u128,
    impeded_move: bool,
    previous_box_position: Option<BoxPosition>,
}

impl PartialOrd for Label {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Label {
    fn cmp(&self, other: &Self) -> Ordering {
        self.impeded_move
            .cmp(&other.impeded_move)
            .then_with(|| self.non_impeded_moves.cmp(&other.non_impeded_moves))
    }
}

impl Storage {
    fn new(width: usize, depth: usize, height: usize) -> Storage {
        Storage {
            width,
            depth,
            height,
            box_positions: HashMap::new(),
            matrix: vec![vec![vec![MatrixPosition::NotOccupied; height]; depth]; width],
        }
    }

    fn add_box_unchecked(&mut self, box_id: BoxId, box_position: BoxPosition) {
        self.box_positions.insert(box_id, box_position);
        self.matrix[box_position.x][box_position.y][box_position.z] =
            MatrixPosition::Occupied(box_id);
    }

    fn move_box(&mut self, box_move: BoxMove) -> Result<(), ()> {
        if !self.is_valid_move(box_move) {
            return Err(());
        }

        self.matrix[box_move.source_box_position.x][box_move.source_box_position.y]
            [box_move.source_box_position.z] = MatrixPosition::NotOccupied;
        self.matrix[box_move.destination_box_position.x][box_move.destination_box_position.y]
            [box_move.destination_box_position.z] = MatrixPosition::Occupied(box_move.box_id);

        *self
            .box_positions
            .get_mut(&box_move.box_id)
            .ok_or(())
            .unwrap() = box_move.destination_box_position;

        return Ok(());
    }

    fn is_valid_move(&self, box_move: BoxMove) -> bool {
        if self.is_occupied(box_move.destination_box_position) {
            return false;
        }

        if self.is_blocked(box_move.destination_box_position) {
            return false;
        }

        if !self.within_bounds(box_move.destination_box_position) {
            return false;
        }

        if !self.support_below(box_move.destination_box_position) {
            return false;
        }

        if self.box_above(box_move.source_box_position) {
            return false;
        }

        return true;
    }

    fn within_bounds(&self, box_position: BoxPosition) -> bool {
        box_position.x <= self.width && box_position.y < self.depth && box_position.z < self.height
    }

    fn support_below(&self, box_position: BoxPosition) -> bool {
        box_position.z == 0
            || self.is_occupied(BoxPosition {
                x: box_position.x,
                y: box_position.y,
                z: box_position.z - 1,
            })
    }

    fn box_above(&self, box_position: BoxPosition) -> bool {
        box_position.z < self.height - 1
            && self.is_occupied(BoxPosition {
                x: box_position.x,
                y: box_position.y,
                z: box_position.z + 1,
            })
    }

    fn get_box_position(&self, box_id: BoxId) -> Option<BoxPosition> {
        self.box_positions.get(&box_id).cloned()
    }

    fn get_box_id_at_box_position(&self, box_position: BoxPosition) -> Option<BoxId> {
        return self.matrix[box_position.x][box_position.y][box_position.z].box_id();
    }

    fn is_occupied(&self, box_position: BoxPosition) -> bool {
        self.matrix[box_position.x][box_position.y][box_position.z].is_occupied()
    }

    fn is_blocked(&self, box_position: BoxPosition) -> bool {
        self.matrix[box_position.x][box_position.y][box_position.z].is_blocked()
    }

    fn adjacent_box_positions(&self, box_position: BoxPosition) -> Vec<BoxPosition> {
        let raw: [(i8, i8, i8); 4] = [
            (1, 0, 0),
            (-1, 0, 0),
            (0, 1, 0),
            (0, -1, 0),
            //(1, 0, 1),
            //(-1, 0, 1),
            //(0, 1, 1),
            //(0, -1, 1),
            //(1, 0, -1),
            //(-1, 0, -1),
            //(0, 1, -1),
            //(0, -1, -1),
        ];

        return raw
            .into_iter()
            .map(|offset| {
                (
                    box_position.x as i8 + offset.0,
                    box_position.y as i8 + offset.1,
                    box_position.z as i8 + offset.2,
                )
            })
            .filter(|(x, y, z)| (*x >= 0) && (*y >= 0) && (*z >= 0))
            .map(|(x, y, z)| (x as usize, y as usize, z as usize))
            .filter(|(x, y, z)| (*x < self.width) && (*y < self.width) && (*z < self.height))
            //.filter(|(x, y, z)| {
            //self.is_valid_move(BoxMove {
            //box_id: 0,
            //source_box_position: box_position,
            //destination_box_position: BoxPosition {
            //x: *x,
            //y: *y,
            //z: *z,
            //},
            //})
            //})
            .map(|(x, y, z)| BoxPosition { x, y, z })
            .collect();
    }

    fn block_box_position(&mut self, box_position: BoxPosition) -> Result<(), ()> {
        if self.is_occupied(box_position) {
            return Err(());
        }

        self.matrix[box_position.x][box_position.y][box_position.z] = MatrixPosition::Blocked;
        return Ok(());
    }
}

fn get_shortest_box_route(
    box_id: BoxId,
    target_box_position: BoxPosition,
    storage: &Storage,
) -> Option<Vec<BoxMove>> {
    let mut storage = storage.clone();

    let shortest_route_can_phase =
        get_shortest_box_route_can_phase(box_id, target_box_position, &storage)?;

    //important to block the non-phase box_position on the path
    for (base_box_position, label) in shortest_route_can_phase.iter() {
        if !label.impeded_move {
            let _ = storage.block_box_position(*base_box_position);
        }
    }

    let mut offset_moves = Vec::new();

    for (base_box_position, label) in shortest_route_can_phase.iter() {
        if label.impeded_move {
            match storage
                .adjacent_box_positions(*base_box_position)
                .iter()
                .find_map(|adjacent_box_position| {
                    let offset_box_move = BoxMove {
                        box_id: storage
                            .get_box_id_at_box_position(*base_box_position)
                            .unwrap(),
                        source_box_position: *base_box_position,
                        destination_box_position: *adjacent_box_position,
                    };

                    if storage.is_valid_move(offset_box_move) {
                        Some(offset_box_move)
                    } else {
                        None
                    }
                }) {
                Some(found_offset_box_move) => {
                    storage.move_box(found_offset_box_move).unwrap();
                    offset_moves.push(found_offset_box_move);
                }
                None => {
                    return None;
                }
            }
        }
    }

    let mut route_moves = shortest_route_can_phase
        .into_iter()
        .tuple_windows()
        .map(
            |((source_box_position, _), (destination_box_position, _))| BoxMove {
                box_id,
                source_box_position,
                destination_box_position,
            },
        )
        .collect::<Vec<_>>();

    offset_moves.append(&mut route_moves);
    return Some(
        offset_moves
            .into_iter()
            .map(|box_move| box_move.simplify())
            .flatten()
            .collect(),
    );
}

fn get_shortest_box_route_can_phase(
    box_id: BoxId,
    target_box_position: BoxPosition,
    storage: &Storage,
) -> Option<Vec<(BoxPosition, Label)>> {
    let mut temporary_labels: PriorityQueue<BoxPosition, Reverse<Label>> = PriorityQueue::new();
    let mut permanent_labels = HashMap::new();

    temporary_labels.push_increase(
        storage.get_box_position(box_id)?,
        Reverse(Label {
            impeded_moves: 0,
            non_impeded_moves: 0,
            previous_box_position: None,
            impeded_move: false,
        }),
    );

    while let Some((base_box_position, Reverse(base_label))) = temporary_labels.pop() {
        permanent_labels.insert(base_box_position, base_label);

        if base_box_position == target_box_position {
            return Some(trace_back(base_box_position, base_label, &permanent_labels));
        }

        for adjacent_box_position in storage.adjacent_box_positions(base_box_position) {
            if !permanent_labels.contains_key(&adjacent_box_position) {
                if !storage.is_occupied(adjacent_box_position) {
                    temporary_labels.push_increase(
                        adjacent_box_position,
                        Reverse(Label {
                            impeded_moves: base_label.impeded_moves,
                            non_impeded_moves: base_label.non_impeded_moves + 1,
                            impeded_move: false,
                            previous_box_position: Some(base_box_position),
                        }),
                    );
                } else if !storage.box_above(adjacent_box_position) {
                    temporary_labels.push_increase(
                        adjacent_box_position,
                        Reverse(Label {
                            impeded_moves: base_label.impeded_moves + 1,
                            non_impeded_moves: base_label.non_impeded_moves,
                            impeded_move: true,
                            previous_box_position: Some(base_box_position),
                        }),
                    );
                }
            }
        }
    }

    return None;
}

fn trace_back(
    final_box_position: BoxPosition,
    final_label: Label,
    permanent_labels: &HashMap<BoxPosition, Label>,
) -> Vec<(BoxPosition, Label)> {
    let mut label_path = Vec::from([(final_box_position, final_label)]);

    let mut current_label = final_label;
    while let Some(next_box_position) = current_label.previous_box_position {
        current_label = *permanent_labels.get(&next_box_position).unwrap();

        label_path.push((next_box_position, current_label));
    }

    label_path.reverse();

    return label_path;
}
