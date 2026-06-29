# Project_Ca_Nhan: Mô phỏng các nhóm thuật toán trí tuệ nhân tạo

Project này xây dựng giao diện trực quan để mô phỏng và so sánh các nhóm thuật toán trí tuệ nhân tạo trên nhiều dạng bài toán khác nhau. Mục tiêu chính là minh họa cách các thuật toán tìm kiếm, tối ưu, thỏa mãn ràng buộc và tìm kiếm đối kháng hoạt động thông qua giao diện tương tác.

## 1. Tổng quan project

Project gồm 3 đề tài chính:

| STT | Đề tài | Thư mục | Nội dung mô phỏng |
| --- | --- | --- | --- |
| 1 | Tìm kiếm trạng thái cho agent | `ai_agent_visualizer_project_fixed` | 8-puzzle, Vacuum World và Belief-State Vacuum |
| 2 | Bài toán thỏa mãn ràng buộc CSP | `to-mau` | Tô màu bản đồ TP. Hồ Chí Minh |
| 3 | Tìm kiếm đối kháng trong trò chơi | `caro` | Game Caro 15x15 người chơi với AI |

Trong đó, module tìm kiếm trạng thái có 2 môi trường minh họa:

- `8-puzzle`: tìm chuỗi hành động để đưa bàn cờ về trạng thái đích.
- `Vacuum World`: robot di chuyển, hút bụi, tránh vật cản và dừng khi môi trường sạch.

## 2. Sáu nhóm thuật toán được áp dụng

| Nhóm | Tên nhóm thuật toán | Thuật toán trong project | Áp dụng vào |
| --- | --- | --- | --- |
| 1 | Tìm kiếm không thông tin | BFS1, BFS2, DFS1, DFS2, UCS, IDS | 8-puzzle, Vacuum World |
| 2 | Tìm kiếm có thông tin / heuristic search | Greedy Best-First Search, A*, IDA* | 8-puzzle, Vacuum World |
| 3 | Tìm kiếm cục bộ | Simple Hill Climbing, Steepest Hill Climbing, Stochastic Hill Climbing, Random Restart Hill Climbing, Local Beam Search, Simulated Annealing | 8-puzzle, Vacuum World |
| 4 | Tìm kiếm trong môi trường không xác định / quan sát không đầy đủ | AND-OR Graph Search; Belief-State BFS cho Vacuum | 8-puzzle, Vacuum World |
| 5 | Bài toán thỏa mãn ràng buộc CSP | Backtracking, Forward Checking, AC-3/MAC, Min-Conflicts | Tô màu bản đồ |
| 6 | Tìm kiếm đối kháng | Minimax, Alpha-Beta Pruning, Expectimax | Caro |

### 2.1. Mô tả ngắn các thuật toán

#### Nhóm tìm kiếm không thông tin

- `BFS1`: duyệt theo chiều rộng bằng hàng đợi FIFO, kiểm tra goal khi node được lấy ra khỏi frontier. Thuật toán tìm được lời giải nông nhất nếu chi phí bước đi bằng nhau.
- `BFS2`: biến thể BFS kiểm tra goal ngay khi sinh node con. Cách này thường dừng sớm hơn BFS1 vì không cần đợi goal được pop khỏi frontier.
- `DFS1`: duyệt theo chiều sâu bằng stack LIFO, kiểm tra goal khi node được lấy ra khỏi stack. Trong project có giới hạn độ sâu để tránh đi quá sâu hoặc lặp lâu.
- `DFS2`: biến thể DFS kiểm tra goal ngay khi sinh node con. Thuật toán vẫn có thể không tìm được lời giải nếu bị giới hạn độ sâu hoặc chọn nhánh không thuận lợi.
- `UCS`: Uniform-Cost Search, ưu tiên node có tổng chi phí đường đi nhỏ nhất. Trong project, mỗi hành động có cost bằng 1 nên UCS cho kết quả tương tự BFS tối ưu theo số bước.
- `IDS`: Iterative Deepening Search, chạy DFS nhiều lần với độ sâu tăng dần. IDS kết hợp ưu điểm tiết kiệm bộ nhớ của DFS và khả năng tìm lời giải nông như BFS.

#### Nhóm tìm kiếm có thông tin

- `GREEDY`: Greedy Best-First Search, chọn node có heuristic nhỏ nhất. Thuật toán thường chạy nhanh nhưng không đảm bảo tối ưu.
- `ASTAR`: A* Search, chọn node theo `f(n) = g(n) + h(n)`. Với heuristic phù hợp, A* có thể tìm lời giải tối ưu hiệu quả hơn BFS/UCS.
- `IDA*`: Iterative Deepening A*, kết hợp ý tưởng A* với tìm kiếm sâu dần theo ngưỡng `f`. Thuật toán tiết kiệm bộ nhớ hơn A* nhưng có thể lặp lại nhiều node.

#### Nhóm tìm kiếm cục bộ

- `SIMPLE HC`: Simple Hill Climbing, chọn láng giềng đầu tiên cải thiện điểm heuristic. Thuật toán đơn giản nhưng dễ kẹt tại local optimum.
- `STEEPEST HC`: Steepest Ascent Hill Climbing, xét các láng giềng và chọn trạng thái cải thiện tốt nhất. Cách này kỹ hơn Simple HC nhưng vẫn có thể kẹt plateau/local optimum.
- `STOCHASTIC HC`: Stochastic Hill Climbing, chọn ngẫu nhiên một láng giềng có cải thiện. Thuật toán có yếu tố ngẫu nhiên nên kết quả có thể khác nhau giữa các lần chạy.
- `RANDOM RESTART HC`: chạy Hill Climbing nhiều lần từ các trạng thái khởi đầu khác nhau để tăng khả năng thoát local optimum.
- `LOCAL BEAM`: giữ đồng thời `k` trạng thái tốt nhất ở mỗi vòng lặp. Thuật toán mở rộng nhiều hướng cùng lúc thay vì chỉ đi theo một trạng thái hiện tại.
- `SIMULATED ANNEALING`: chọn cả bước đi xấu hơn với một xác suất phụ thuộc nhiệt độ. Khi nhiệt độ giảm dần, thuật toán chuyển từ khám phá rộng sang khai thác cục bộ.

#### Nhóm môi trường không xác định / quan sát không đầy đủ

- `AND-OR GRAPH`: tìm kế hoạch có điều kiện trong môi trường có thể có nhiều kết quả sau một hành động. OR node biểu diễn lựa chọn hành động, AND node biểu diễn các kết quả đều phải được xử lý.
- `BELIEF-STATE BFS`: tìm kiếm trên belief state cho Vacuum. Một belief state là tập các trạng thái môi trường có thể xảy ra khi agent không biết chắc bản đồ bụi; thuật toán tìm một chuỗi hành động làm sạch mọi khả năng.

#### Nhóm CSP

- `Backtracking`: gán màu lần lượt cho từng biến, nếu vi phạm ràng buộc thì quay lui. Đây là cách cơ bản để giải bài toán thỏa mãn ràng buộc.
- `Forward Checking`: sau khi gán một biến, thuật toán loại màu không hợp lệ khỏi miền giá trị của các biến láng giềng chưa gán. Nhờ đó phát hiện xung đột sớm hơn Backtracking thuần.
- `AC-3/MAC`: duy trì tính nhất quán cung giữa các biến. Khi miền giá trị bị thu hẹp, thuật toán tiếp tục lan truyền ràng buộc đến các cung liên quan.
- `Min-Conflicts`: bắt đầu với một assignment đầy đủ, sau đó liên tục chọn biến đang xung đột và đổi sang giá trị gây ít xung đột nhất. Thuật toán phù hợp với CSP lớn và có yếu tố ngẫu nhiên.

#### Nhóm tìm kiếm đối kháng

- `Minimax`: giả định AI và người chơi đều chọn nước đi tối ưu. AI chọn nước đi tối đa hóa điểm, còn đối thủ được xem là bên tối thiểu hóa điểm của AI.
- `Alpha-Beta Pruning`: tối ưu Minimax bằng cách cắt bỏ các nhánh chắc chắn không ảnh hưởng đến quyết định cuối cùng. Kết quả logic giống Minimax nhưng thường duyệt ít node hơn.
- `Expectimax`: mở rộng Minimax bằng cách mô hình hóa đối thủ như nút xác suất. Thay vì luôn chọn nước đi gây bất lợi nhất cho AI, thuật toán lấy giá trị kỳ vọng của các nước đi có thể xảy ra.

## 3. Cấu trúc thư mục

```text
Project_Ca_Nhan/
|-- README.md
|-- ai_agent_visualizer_project_fixed/
|   |-- main.py
|   |-- algorithms/
|   |-- problems/
|   `-- ui/
|-- to-mau/
|   |-- main.py
|   |-- gui.py
|   |-- backtracking.py
|   |-- forward_checking.py
|   |-- ac3.py
|   `-- min_conflicts.py
`-- caro/
    |-- main.py
    |-- gui.py
    |-- game.py
    |-- algorithms.py
    `-- README.md
```

## 4. Cách chạy project

Yêu cầu:

- Python 3.10 trở lên.
- Tkinter, thường đã có sẵn khi cài Python trên Windows.
- Không cần cài thêm thư viện ngoài.

### 4.1. Chạy mô phỏng 8-puzzle và Vacuum World

```bash
cd ai_agent_visualizer_project_fixed
python main.py
```

Chức năng chính:

- Chọn bài toán: `8-PUZZLE` hoặc `VACUUM`.
- Chọn thuật toán trong danh sách.
- Nhấn `APPLY` để thuật toán tìm lời giải và giao diện tự động mô phỏng từng bước.
- Có bảng trace hiển thị node hiện tại, frontier, reached và ghi chú thuật toán.
- Có thể điều khiển thủ công bằng `W/A/S/D`, phím `Space` với Vacuum, hoặc click chuột lên board.

### 4.2. Chạy mô phỏng tô màu bản đồ

```bash
cd to-mau
python main.py
```

Chức năng chính:

- Hiển thị đồ thị quan hệ giáp ranh giữa các quận/huyện.
- Mô phỏng quá trình tô màu bằng các thuật toán CSP.
- Giao diện hiển thị màu hiện tại, miền giá trị còn lại và log từng bước.

Các thuật toán hỗ trợ:

- Backtracking Search
- Forward Checking
- AC-3/MAC
- Min-Conflicts

### 4.3. Chạy game Caro với AI

```bash
cd caro
python main.py
```

Chức năng chính:

- Người chơi là `X`, AI là `O`.
- Chọn thuật toán AI: Minimax, Alpha-Beta hoặc Expectimax.
- Có thể chỉnh độ sâu tìm kiếm và số lượng nước đi ứng viên.
- Giao diện hiển thị bàn cờ, trạng thái ván chơi và log kết quả tìm kiếm của AI.

## 5. Mô tả từng module

### 5.1. AI Agent Visualizer

Module này dùng để mô phỏng các thuật toán tìm kiếm trên không gian trạng thái.

Với `8-puzzle`, mỗi trạng thái là một cách sắp xếp 9 ô, trong đó ô `0` là ô trống. Mục tiêu là đưa bàn cờ về trạng thái:

```text
1 2 3
4 5 6
7 8 _
```

Với `Vacuum World`, trạng thái gồm vị trí robot và ma trận môi trường 3x3. Robot có thể:

- Di chuyển lên, xuống, trái, phải nếu không gặp vật cản.
- Hút bụi tại ô hiện tại.
- Kết thúc khi tất cả ô bụi đã được làm sạch.

Với `Belief-State Vacuum`, agent biết vị trí hiện tại và vị trí vật cản, nhưng không biết chắc ô nào có bụi. Một belief state là tập hợp các trạng thái môi trường có thể xảy ra. Thuật toán `BELIEF-STATE BFS` tìm một chuỗi hành động có thể làm sạch tất cả các khả năng trong belief state, tức là một kế hoạch phù hợp cho môi trường quan sát không đầy đủ.

Module này minh họa rõ các khái niệm:

- State
- Action
- Successor
- Goal test
- Frontier
- Reached set
- Search trace
- Solution path
- Belief state

### 5.2. Tô màu bản đồ

Module này biểu diễn bài toán tô màu bản đồ dưới dạng CSP:

- Biến: các quận/huyện.
- Miền giá trị: tập màu có thể chọn.
- Ràng buộc: hai khu vực giáp ranh không được có cùng màu.

Các thuật toán CSP trong project cho thấy sự khác nhau giữa:

- Thử và quay lui thuần túy.
- Cắt tỉa miền giá trị bằng Forward Checking.
- Lan truyền ràng buộc bằng AC-3/MAC.
- Tối ưu xung đột bằng Min-Conflicts.

### 5.3. Caro

Module này mô phỏng bài toán tìm kiếm trong môi trường đối kháng:

- Người chơi và AI có mục tiêu trái ngược nhau.
- AI đánh giá trạng thái bàn cờ bằng heuristic.
- AI chọn nước đi dựa trên thuật toán tìm kiếm.

Các thuật toán:

- `Minimax`: giả định người chơi luôn chọn nước đi tối ưu để chống lại AI.
- `Alpha-Beta`: tối ưu Minimax bằng cách cắt tỉa các nhánh không cần xét.
- `Expectimax`: mô hình hóa đối thủ như một nút xác suất, lấy giá trị kỳ vọng.

## 6. Kết quả kiểm tra

Project đã được kiểm tra các nội dung chính:

- Toàn bộ file Python compile thành công, không có lỗi cú pháp.
- 8-puzzle và Vacuum World chạy được trên giao diện Tkinter.
- Các thuật toán BFS, UCS, IDS, A*, Greedy, IDA* tìm được đường đi hợp lệ trên trạng thái mặc định.
- Belief-State BFS tìm được kế hoạch làm sạch cho Vacuum World khi agent chưa biết chắc bản đồ bụi.
- Các thuật toán local search hoạt động đúng bản chất, có thể tìm lời giải hoặc dừng ở local optimum.
- Tô màu bản đồ trả về nghiệm hợp lệ, không có hai khu vực giáp ranh trùng màu.
- Caro kiểm tra thắng ngang, dọc, chéo, phản chéo chính xác.
- AI trong Caro chọn được nước thắng ngay và biết chặn nước nguy hiểm trong các tình huống kiểm thử.

## 7. Lưu ý khi demo và báo cáo

Một số thuật toán không đảm bảo luôn tìm được lời giải trong mọi trường hợp:

- DFS có thể không tìm ra lời giải nếu giới hạn độ sâu hoặc số lần mở rộng chưa đủ.
- Hill Climbing có thể dừng tại local optimum hoặc plateau.
- Simulated Annealing phụ thuộc vào tham số nhiệt độ, tốc độ làm nguội và yếu tố ngẫu nhiên.
- Min-Conflicts cũng có yếu tố ngẫu nhiên, tuy nhiên thường tìm được nghiệm nhanh với bài toán tô màu hiện tại.
- Belief-State BFS có thể tốn nhiều bộ nhớ hơn state search thông thường vì mỗi node là một tập các trạng thái có thể xảy ra.

Vì vậy, khi báo cáo cần phân biệt:

- Nhóm thuật toán đảm bảo tìm lời giải nếu tồn tại và tài nguyên đủ, ví dụ BFS, UCS, A*, IDS.
- Nhóm thuật toán heuristic/local search, có thể chạy nhanh nhưng không luôn đảm bảo tối ưu hoặc tìm được nghiệm.
- Nhóm thuật toán đối kháng, kết quả phụ thuộc vào độ sâu tìm kiếm, heuristic và giới hạn số nước đi ứng viên.

## 8. Gợi ý trình bày trong báo cáo

Có thể trình bày project theo bố cục:

1. Giới thiệu mục tiêu project.
2. Mô tả 3 đề tài áp dụng.
3. Bảng ánh xạ 6 nhóm thuật toán với module tương ứng.
4. Thiết kế giao diện và cách người dùng thao tác.
5. Phân tích thuật toán chính.
6. Kết quả chạy thử và nhận xét.
7. Hạn chế và hướng phát triển.

## 9. Hướng phát triển

Một số hướng có thể mở rộng:

- Thêm biểu đồ so sánh số node mở rộng và thời gian chạy giữa các thuật toán.
- Cho phép người dùng nhập trạng thái 8-puzzle tùy ý.
- Thêm bản đồ khác cho bài toán tô màu.
- Tối ưu heuristic cho Caro để AI đánh tốt hơn.
- Lưu lại lịch sử chạy thuật toán để phục vụ báo cáo/thống kê.
