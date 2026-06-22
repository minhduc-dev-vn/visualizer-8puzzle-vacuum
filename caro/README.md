# Caro - tim kiem trong moi truong doi khang

Mini project ap dung 3 thuat toan tim kiem vao tro choi Caro 15x15:

- Minimax
- Alpha-Beta pruning
- Expectimax

Nguoi choi la `X`, may la `O`. May dung ham danh gia heuristic de chon nuoc di tot nhat theo thuat toan duoc chon.

## Cach chay

```bash
python main.py
```

Neu dang o thu muc goc repo:

```bash
cd Bai-tap-ve-nha/caro
python main.py
```

## Cau truc file

- `main.py`: diem khoi chay giao dien.
- `gui.py`: giao dien Tkinter, choi nguoi voi may, chon thuat toan/do sau.
- `game.py`: luat Caro, kiem tra thang/thua, sinh nuoc di ung vien, ham danh gia ban co.
- `algorithms.py`: cai dat `minimax_decision`, `alphabeta_decision`, `expectimax_decision`.

## Tom tat thuat toan

- Minimax: xem AI la nut MAX va doi thu la nut MIN.
- Alpha-Beta: van dua tren Minimax nhung cat nhanh cac nhanh khong the anh huong den ket qua.
- Expectimax: AI la nut MAX, doi thu duoc mo hinh hoa nhu nut co xac suat, lay gia tri ky vong cua cac nuoc di ung vien.

## Ghi chu hieu nang

Caro 15x15 co he so phan nhanh rat lon, nen chuong trinh chi xet cac o trong nam gan nhung quan da danh. Tham so `Candidate limit` gioi han so nuoc di tot nhat duoc mo rong o moi nut, giup thuat toan chay duoc trong giao dien.
