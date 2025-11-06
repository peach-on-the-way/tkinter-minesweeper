# Converts DNF to CNF
#
# Some preemptive elimination is necessary to be able to compute 
# the CNF clauses within reasonble amount of memory and time.
#
# It's the bottleneck.
def convert_normal_form(form):
    def inner(first_clause, tail_clauses):
        # Use set to eliminate a or a within a clause.
        if len(tail_clauses) == 0:
            return set(frozenset(set([x])) for x in first_clause)

        form = set() 
        for tail_atoms in inner(tail_clauses[0], tail_clauses[1:]):
            for first_atom in first_clause:
                # Eliminate clause that contains ~a or a 
                if -first_atom in tail_atoms:
                    continue
                form.add(frozenset(set([first_atom]) | tail_atoms))
        return form

    return inner(form[0], form[1:])

# Remove duplicate clause to reduce memory usage.
def dedup(clauses):
    new_clauses = set()
    for clause in clauses:
        clause = set(clause)
        eliminate_clause = False
        for atom in clause:
            # Eliminate clauses that contains ~a or a again just in case.
            if atom < 0 and -atom in clause:
                eliminate_clause = True
                break
        if eliminate_clause:
            continue
        new_clauses.add(frozenset(clause))
    return [list(clause) for clause in new_clauses]

# Sort a bit so it's easier to inspect some patterns in case we were able
# to generate CNF clause directly without going through the DNF->CNF conversion
# in the future.
def sort(clauses):
    for clause in clauses:
        clause.sort(key=lambda a: -a if a < 0 else a)

    def key(clause):
        l = len(clause) * 10000
        # if len(clause[0]) == 1:
        #     l += ord('1') - ord(clause[0]) + 1
        for i, atom in enumerate(clause):
            if atom < 0:
                l -= 2**i
        return l

    clauses.sort(reverse=True, key=key)

# Attempts to generate combinations of possible mine locations in DNF clause.
def generate_mine_dnf_clauses(cells, mines_count):
    def inner(current_clause, cells, mines_count):
        if len(cells) == 0:
            clauses = set([frozenset(current_clause)])
            return clauses

        if mines_count > 0:
            # There are more mine positions we can combine.
            clauses = set()
            for x in cells:
                tail_clauses = inner(
                    current_clause | set([x]),
                    cells - set([x]),
                    mines_count - 1,
                )
                clauses = clauses | tail_clauses
            return clauses
        else:
            # Mines positions has been taken over by other cells
            # Return the rest negated, e.g. not a mine.
            clause = current_clause | set([-x for x in cells])
            return set([frozenset(clause)])

    clauses = inner(set(), cells, mines_count)
    return [list(clause) for clause in clauses]

def generate(cell_count, mines_count):
    cells = [i for i in range(1, 1 + cell_count)]

    dnf = generate_mine_dnf_clauses(set(cells), mines_count)

    cnf = convert_normal_form(dnf)
    cnf = dedup(cnf)
    sort(cnf)

    with open(f"cache/{cell_count}_{mines_count}", "w", encoding="utf-8") as f:
        for clause in cnf:
            for atom in clause:
                f.write(f"{atom:>2} ")
            f.write(f"\n")
         # Specifiy an ending marker in case the programs stops midway for whatever reasons
         # to prevent from incomplete CNF being in used
        f.write(f"=")

    print(f"{cell_count} {mines_count} finished")

from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=16) as e:
    for cell_count in range(1, 13):
        for mines_count in range(0, cell_count + 1):
            e.submit(generate, cell_count, mines_count)

