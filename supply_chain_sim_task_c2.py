import random
import numpy as np
import supply_chain_sim_task_a2 as task_a
import supply_chain_sim_task_b2 as task_b
import supply_chain_sim_task_c1 as task_c


def experiments(task_module, seeds=range(100)):

    C, N, R = [], [], []

    for seed in seeds:
        random.seed(seed)
        sim = task_module.Simulation()
        sim.run()

        d1 = sim.distributors["D1"]
        Ci = sum(d1.total_cost_per_day.values())
        Ni = sum(
            d1.sales_per_day[d][p]
            for d in range(task_module.TOTAL_DAYS)
            for p in task_module.PRODUCTS
        )
        Ri = Ci / Ni if Ni > 0 else float("inf")

        C.append(Ci)
        N.append(Ni)
        R.append(Ri)

    return {
        "C_mean": float(np.mean(C)),
        "C_std": float(np.std(C)),
        "N_mean": float(np.mean(N)),
        "N_std": float(np.std(N)),
        "R_mean": float(np.mean(R)),
        "R_std": float(np.std(R)),
    }


def main():
    results = {
        "Task a (Simple order strategy)": experiments(task_a),
        "Task b (On-demand order strategy)": experiments(task_b),
        "Task c (Order delay strategy)": experiments(task_c),
    }

    headers = ["Strategy", "C mean", "C dev", "N mean", "N dev", "R mean", "R dev"]
    first_col = max(len(headers[0]), max(len(k) for k in results.keys()))
    col_widths = [first_col, 12, 12, 12, 12, 12, 12]

    def fmt_row(values):
        out = []
        for v, w in zip(values, col_widths):
            if isinstance(v, (int, float)):
                out.append(f"{v:>{w}.3f}")
            else:
                out.append(f"{v:<{w}}")
        return " | ".join(out)

    print(fmt_row(headers))
    print("-" * (sum(col_widths) + 3 * (len(col_widths) - 1)))

    for strategy, s in results.items():
        print(
            fmt_row(
                [
                    strategy,
                    s["C_mean"],
                    s["C_std"],
                    s["N_mean"],
                    s["N_std"],
                    s["R_mean"],
                    s["R_std"],
                ]
            )
        )


if __name__ == "__main__":
    main()
