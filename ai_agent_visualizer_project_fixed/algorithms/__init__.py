from algorithms.bfs1 import search as bfs1
from algorithms.bfs2 import search as bfs2
from algorithms.dfs1 import search as dfs1
from algorithms.dfs2 import search as dfs2
from algorithms.ids import search as ids
from algorithms.ida_star import search as ida_star
from algorithms.ucs import search as ucs
from algorithms.astar import search as astar
from algorithms.greedy import search as greedy
from algorithms.hill_climbing import search_simple as simple_hill_climbing
from algorithms.hill_climbing import search_steepest as steepest_hill_climbing
from algorithms.hill_climbing import search_stochastic as stochastic_hill_climbing
from algorithms.hill_climbing import search_random_restart as random_restart_hill_climbing
from algorithms.hill_climbing import search_local_beam as local_beam_search

ALGORITHMS = {
    "BFS1": bfs1,
    "BFS2": bfs2,
    "DFS1": dfs1,
    "DFS2": dfs2,
    "IDS": ids,
    "IDA*": ida_star,
    "UCS": ucs,
    "ASTAR": astar,
    "GREEDY": greedy,
    "SIMPLE HC": simple_hill_climbing,
    "STEEPEST HC": steepest_hill_climbing,
    "STOCHASTIC HC": stochastic_hill_climbing,
    "RANDOM RESTART HC": random_restart_hill_climbing,
    "LOCAL BEAM": local_beam_search,
}
