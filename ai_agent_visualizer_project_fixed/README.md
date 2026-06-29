# AI Agent Visualizer

Tkinter app de mo phong cac thuat toan tim kiem cho:

- 8-Puzzle
- Vacuum World (3x3)
- Belief-State Vacuum World (sensorless/partially observable)

## Thuat toan ho tro

- `BFS1`: check goal khi node duoc pop khoi frontier.
- `BFS2`: check goal ngay khi sinh node con.
- `DFS1`: DFS co depth limit, check goal khi pop.
- `DFS2`: DFS co depth limit, check goal khi sinh con.
- `IDS`: Iterative Deepening Search (depth limit tang dan).
- `IDA*`: Iterative Deepening A*.
- `UCS`: Uniform-Cost Search.
- `ASTAR`: A* Search.
- `GREEDY`: Greedy Best-First Search.
- `AND-OR GRAPH`: AND-OR Graph Search for conditional plans.
- `SIMPLE HC`: Simple Hill Climbing.
- `STEEPEST HC`: Steepest Ascent Hill Climbing.
- `STOCHASTIC HC`: Stochastic Hill Climbing.
- `RANDOM RESTART HC`: Random Restart Hill Climbing.
- `LOCAL BEAM`: Local Beam Search.
- `SIMULATED ANNEALING`: Simulated Annealing local search.
- `BELIEF-STATE BFS`: BFS tren belief state cho Vacuum. Agent biet vi tri robot va vat can, nhung khong biet chac o nao co bui; thuat toan tim mot chuoi hanh dong lam sach moi kha nang.

## Cau truc chinh

```text
ai_agent_visualizer_project_fixed/
|-- main.py
|-- algorithms/
|   |-- __init__.py
|   |-- common.py
|   |-- bfs1.py
|   |-- bfs2.py
|   |-- dfs1.py
|   |-- dfs2.py
|   |-- ids.py
|   |-- ida_star.py
|   |-- ucs.py
|   |-- astar.py
|   |-- greedy.py
|   |-- and_or_graph_search.py
|   |-- vacuum_belief_state.py
|   |-- hill_climbing.py
|   `-- simulated_annealing.py
|-- problems/
|   |-- __init__.py
|   |-- puzzle.py
|   `-- vacuum.py
`-- ui/
    |-- __init__.py
    `-- app.py
```

## Cach chay

Tu thu muc goc repo:

```bash
cd ai_agent_visualizer_project_fixed
python main.py
```

Neu dang dung nhieu ban Python:

```bash
py -3.13 main.py
```

## Search Trace tren UI

Bang trace hien thi day du:

- `Step`
- `Action`
- `Current Node`
- `Frontier - FULL`
- `Reached - FULL`
- `Note`

UI co thanh cuon ngang/doc va o `Selected trace detail` de xem noi dung dai.

## Dieu khien thu cong

- `W/A/S/D`: di chuyen.
- `Space`: `SUCK` (che do Vacuum).
- Click chuot vao o tren board.

## Ghi chu ve gioi han

- `Max expansions`: gioi han so lan mo rong de tranh treo may.
- `Depth / HC parameter`: depth limit cho `DFS1`, `DFS2`, `IDS`, `IDA*`, `AND-OR GRAPH`; restart count cho `RANDOM RESTART HC`; beam width `k` cho `LOCAL BEAM`; initial temperature `T0` cho `SIMULATED ANNEALING`.
- `BELIEF-STATE BFS` chi nen chay voi che do `VACUUM`. Moi node cua thuat toan la mot tap cac state co the xay ra, nen co the ton bo nho/thoi gian hon state search thong thuong.

Tang qua cao 2 gia tri tren co the lam thuat toan chay rat lau.
