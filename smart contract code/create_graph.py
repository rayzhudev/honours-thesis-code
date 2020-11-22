import sys
import matplotlib
from matplotlib import pyplot as plt
import numpy as np

if __name__ == "__main__":
    if not len(sys.argv) == 3:
        print("results file and y axis required")
        sys.exit()
    file = open(sys.argv[1], "r")
    y_axis_lines = sys.argv[2].split(',')
    fig, ax = plt.subplots()
    
    timestep = []
    tx_ticker = []
    successful_refunds = []
    insured_total = []
    byz_size = []
    com_size = []
    comp_txs = []
    unsuccessful_refunds = []

    lines = file.readlines()
    counter = 1
    for line in lines:
        arr = line.split(',')
        if not arr[0].isdigit():
            continue
        timestep.append(counter)
        counter += 1
        tx_ticker.append(int(arr[0]))
        successful_refunds.append(int(arr[1]))
        insured_total.append(int(arr[2]))
        byz_size.append(int(arr[3]))
        com_size.append(int(arr[4]))
        if len(arr) >= 6:
            comp_txs.append(int(arr[5]))
        if len(arr) >= 7:
            unsuccessful_refunds.append(int(arr[6]))

    cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
    graph_lines = []
    for item in y_axis_lines:
        item = int(item)
        if item == 0:
            a, = ax.plot(timestep, tx_ticker, color=cycle[item], label="txs processed", alpha=0.7)
            graph_lines.append(a)
        # if item == 1:
        #     a, = ax.plot(timestep, successful_refunds, color=cycle[item], label="successful refunds")
        #     graph_lines.append(a)
        if item == 1:
            ax2 = ax.twinx()
            a, = ax2.plot(timestep, successful_refunds, color=cycle[item], label="successful refunds", marker="1")
            # b, = ax2.plot(timestep, unsuccessful_refunds, color=cycle[item+5], label="unsuccessful refunds")
            graph_lines.append(a)
            # graph_lines.append(b)
            ax2.set_ylabel("Successful refunds")
        if item == 2:
            ax2 = ax.twinx()
            a, = ax2.plot(timestep, insured_total, color=cycle[item], label="insured total")
            graph_lines.append(a)
            ax2.set_ylabel("Insured total")
        if item == 3:
            a, = ax.plot(timestep, byz_size, color=cycle[item], label="byzantine nodes", alpha=0.7)
            graph_lines.append(a)
        if item == 4:
            a, = ax.plot(timestep, com_size, '--', color=cycle[item], label="committee nodes", alpha=0.7, linewidth=2)
            graph_lines.append(a)
        if item == 5:
            a, = ax.plot(timestep, comp_txs, color=cycle[item], label="compromised txs")
            graph_lines.append(a)
        if item == 6:
            a, = ax.plot(timestep, unsuccessful_refunds, color=cycle[item], label="unsuccessful refunds")
            graph_lines.append(a)

    # plt.yticks([10, 30, 50, 70, 90, 110, 130, 150, 170, 190, 210, 230])
    # plt.yticks(np.arange(min(insured_total), max(insured_total)+1, 1.0))
    ax.set_xlabel('Timestep')
    ax.set_ylabel('# of unsuccessful refunds, byzantine & committee nodes')
    # ax.legend(graph_lines, [g.get_label() for g in graph_lines], loc="lower left", bbox_to_anchor=(0.5, -0.05), shadow=True, fontsize="small")
    ax.legend(graph_lines, [g.get_label() for g in graph_lines], loc="lower center", bbox_to_anchor=(0.5, -0.4), shadow=True, fontsize="small")
    title_num = str(sys.argv[1].split('_')[1].split('.')[0])
    # plt.title("Simulation " + title_num)
    plt.title("Coalition size 5/10")
    plot_name = sys.argv[1][:-4] + ".png"
    plt.savefig(plot_name, dpi=100, bbox_inches="tight")
    # plt.show()
    file.close()