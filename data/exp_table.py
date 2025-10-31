
def generate_exp_table(max_level = 200):
    exp_table = [0]
    base = 15

    for level in range(2, max_level + 1):
        exp_needed = int(base * (level - 1) ** 2.5)
        exp_table.append(exp_needed)

    return exp_table

exp_table = generate_exp_table()