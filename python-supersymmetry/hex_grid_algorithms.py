from itertools import repeat, product


def grid_spiral(n):
    x = (0, 0, 0)
    vectors = []
    
    def step(direction, i_, add_it=True):
        nonlocal x
        for k in range(i_):
            x = tuple(xi + di for xi, di in zip(x, direction))
            if add_it:
                vectors.append(x)
    
    step((0, 0, 0), 1)
    for i in range(1, n+1):
        step((+1, +0, +0), 1, add_it=False)
        step((+0, +1, +0), i)
        step((-1, +0, +0), i)
        step((+0, +0, -1), i)
        step((+0, -1, +0), i)
        step((+1, +0, +0), i)
        step((+0, +0, +1), i)
            
    return vectors


def grid_brute_force(n):
    line = tuple(range(-n, n+1))
    return list(vec for vec in product(line, line, line) if vec[0] + vec[1] == vec[2])


def grid_fast(n):
    return [
        vec for u in range(-n, 0) for vec in zip(repeat(u, 2 * n + 1), range(-n - u, n + 1), range(-n, n + u + 1))
    ] + [
        vec for u in range(n + 1) for vec in zip(repeat(u, 2 * n + 1), range(-n, n - u + 1), range(-n + u, n + 1))
    ]


def grid_redblob(n):
    return [(u, v, u + v) for u in range(-n, n+1) for v in range(max(-n, -u - n), min(n, -u + n) + 1)]
