from algorithms.bfs1 import search as bfs1
from algorithms.bfs2 import search as bfs2
from algorithms.dfs1 import search as dfs1
from algorithms.dfs2 import search as dfs2
from algorithms.ids import search as ids
from algorithms.ucs import search as ucs
from algorithms.astar import search as astar
from algorithms.greedy import search as greedy

ALGORITHMS = {
    "BFS1": bfs1,
    "BFS2": bfs2,
    "DFS1": dfs1,
    "DFS2": dfs2,
    "IDS": ids,
    "UCS": ucs,
    "ASTAR": astar,
    "GREEDY": greedy,
}
