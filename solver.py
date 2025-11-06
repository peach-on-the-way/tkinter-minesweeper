from pysat.formula import CNF
from pysat.solvers import Solver

dpos = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]

cache_directory = "cnf_cache"

cache = {}

# Return True if cache exists, False otherwise.
def load_cache(cells_count, mines_count):
    cnf = []
    path = f"{cache_directory}/{cells_count}_{mines_count}"
    try:
        f = open(path)
    except OSError as e:
        return False

    print(f"Loading {path}")
    for line in f:
        if line.startswith("="):
            break
        clause = filter(lambda x: x != '', line.strip().split(" "))
        clause = map(int, clause)
        cnf.append(list(clause))
    cache[(cells_count, mines_count)] = cnf
    return True


def get_cached_cnf(cells_count, mines_count):
    if not (cells_count, mines_count) in cache:
        has_cache = load_cache(cells_count, mines_count)
        if not has_cache:
            return None

    return cache[(cells_count, mines_count)]

# The translate the atoms within local CNF from the cache
# to atoms that uniquely represent the cells
def translate_cached_cnf(cnf, cell_ids, mines_count):
    new_cnf = []
    for clause in cnf:
        new_clause = []
        for atom in clause:
            if atom < 0:
                new_atom = -cell_ids[(-atom) - 1]
            else:
                new_atom = cell_ids[atom - 1]
            new_clause.append(new_atom)
        new_cnf.append(new_clause)
    return new_cnf

def get_cnf(cell_names, mines_count):
    cnf = get_cached_cnf(len(cell_names), mines_count)
    if cnf == None:
        return None
    return translate_cached_cnf(cnf, cell_names, mines_count)


def solve_once(board):
    # Converts (x, y) positions to the integer format accepted by pysat
    def pos_to_atom(x, y, board_width):
        index = y * board_width + x
        return index + 1

    def atom_to_pos(index, board_width):
        index = index - 1
        return (index % board_width, index // board_width)

    adjacent_cnf = CNF()

    number_cells_to_check = board.find_number_cells_adjacent_to_unrevealed_cell()
    for x, y in number_cells_to_check:
        flagged_neighbor = set()
        unrevealed_neighbor = set()
        for dx, dy in dpos:
            testx = x + dx
            testy = y + dy
            if not board.pos_inside_board(testx, testy):
                continue
            if board.cell_is_flagged(testx, testy):
                flagged_neighbor.add((testx, testy))
            if not board.cell_is_revealed(testx, testy):
                unrevealed_neighbor.add((testx, testy))

        # Or also called the number for the number cell
        mine_nearby_count = board.cells_grid_info[x][y]

        unrevealed_neighbor = [pos_to_atom(x, y, board.board_size) for x, y in unrevealed_neighbor] 
        adjacent_cnf_clauses = get_cnf(unrevealed_neighbor, mine_nearby_count)
        if adjacent_cnf_clauses == None:
            print("A CNF Clause is unavailable")
            return None
        adjacent_cnf.extend(adjacent_cnf_clauses)

    solver = Solver(bootstrap_with=adjacent_cnf)

    # All the cells that both the agent and user has flagged is assumed
    # to be mines.
    cells_flagged_assumed_mine = { pos_to_atom(x, y, board.board_size) for x, y in board.cells_flagged_locations }

    solver.solve(assumptions=list(cells_flagged_assumed_mine))
    if not solver.solve():
        return None

    # Exhaustive checks
    # If an assignment of a cell is negated and the solution is unsatisfiable,
    # then that cell must not be changed, e.g.
    #     1. The first model for a specific cell is false
    #     2. Try solve again but assumed to be true
    #     3. If the result is unsatisfiable -> The cell must be false, e.g. the cell must be empty
    #     3. If the result is satisfiable -> The cell could either be empty or a mine
    # or
    #     1. The first model for a specific cell is true
    #     2. Try solve again but assumed to be false
    #     3. If the result is unsatisfiable -> The cell must be true, e.g. the cell must be a mine
    #     3. If the result is satisfiable -> The cell could either be empty or a mine

    safe_model = set()

    initial_model = solver.get_model()
    for initial_atom in initial_model:
        if initial_atom in cells_flagged_assumed_mine:
            continue
        satisfiable = solver.solve(assumptions=set([-initial_atom]) | cells_flagged_assumed_mine)
        if not satisfiable:
            safe_model.add(initial_atom)

    # Attempting to solve from known leftover mines.
    if len(safe_model) == 0:
        print("Solving leftover")
        all_unknown_cells = board.cells_unrevealed - board.cells_flagged_locations
        all_unknown_cells = { pos_to_atom(x, y, board.board_size) for x, y in all_unknown_cells }
        mines_left = len(board.mine_locations) - len(board.cells_flagged_locations)

        mines_left_cnf = get_cnf(list(all_unknown_cells), mines_left)
        if mines_left_cnf == None:
            print(f"No cached cnf clause for {len(all_unknown_cells)} cells with {mines_left} mines exists")
            return None


        mines_left_cnf = CNF(from_clauses=mines_left_cnf)
        # Combines with previous adjacent CNF
        mines_left_cnf.extend(adjacent_cnf) 

        solver = Solver(bootstrap_with=mines_left_cnf)
        cells_flagged_assumed_mine = { pos_to_atom(x, y, board.board_size) for x, y in board.cells_flagged_locations }
        solver.solve(assumptions=list(cells_flagged_assumed_mine))
        if not solver.solve():
            # No valid solution possible without guessing
            return None

        # Exhaustive checks, same as previously
        initial_model = solver.get_model()
        for initial_atom in initial_model:
            if initial_atom in cells_flagged_assumed_mine:
                continue
            satisfiable = solver.solve(assumptions=set([-initial_atom]) | cells_flagged_assumed_mine)
            if not satisfiable:
                safe_model.add(initial_atom)

        # Rarely a board can be solved from leftover so an annoucement is exciting
        if len(safe_model) > 0:
            print("Solution found from leftover")

    if len(safe_model) == 0:
        # No valid solution possible without guessing
        return None

    # Safe solution found
    result = {}
    for atom in safe_model:
        if atom > 0:
            is_mine = True
            pos = atom_to_pos(atom, board.board_size)
        else:
            is_mine = False
            pos = atom_to_pos(-atom, board.board_size)
        result[pos] = is_mine
    return result
