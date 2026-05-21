# AI Agent Visualizer

Python Tkinter GUI dùng để mô phỏng BFS/DFS cho:

- 8-Puzzle
- Vacuum World

## Cấu trúc file

```text
ai_agent_visualizer_project/
├── main.py
├── algorithms/
│   ├── __init__.py
│   ├── common.py
│   ├── bfs1.py
│   ├── bfs2.py
│   ├── dfs1.py
│   └── dfs2.py
├── problems/
│   ├── __init__.py
│   ├── puzzle.py
│   └── vacuum.py
└── ui/
    ├── __init__.py
    └── app.py
```

## Chạy chương trình

```bash
python main.py
```

Nếu đang ở ngoài thư mục project:

```bash
cd ai_agent_visualizer_project
python main.py
```

## Ý nghĩa thuật toán

### BFS1 / DFS1

Kiểm tra goal khi node được lấy ra khỏi Frontier.

### BFS2 / DFS2

Kiểm tra goal ngay khi node con được sinh ra.

## Bảng Search Trace

Bảng có đầy đủ:

- Step
- Action
- Current Node
- Frontier full
- Reached full
- Note

Không cắt ngắn nội dung Frontier/Reaching. Có thanh cuộn ngang và khung `Selected trace detail` để xem toàn bộ nội dung của dòng đang chọn.

## Điều khiển thủ công

- W: Up
- A: Left
- S: Down
- D: Right
- Space: Suck trong Vacuum
- Click chuột vào ô trên board


## Fix DFS 8-Puzzle

DFS trong 8-Puzzle có thể đi rất sâu vì không gian trạng thái có chu trình.
Bản này thêm `DFS max depth`, mặc định là `12`, để tránh DFS chạy quá lâu hoặc làm giao diện bị đơ.

Nếu muốn thử bài khó hơn, có thể tăng:
- `Max expansions`
- `DFS max depth`

Nhưng không nên tăng quá cao vì DFS không đảm bảo tìm lời giải ngắn nhất và có thể mở rộng rất nhiều node.
