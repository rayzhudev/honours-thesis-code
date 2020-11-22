from matplotlib import pyplot as plt
import numpy as np
import matplotlib as mpl

fig, ax = plt.subplots(figsize=(13,5))
objects = ("5H5R,0.5","5R,0.5","5H3R2B,0.2","8R2B,0.2","5H3R2B,0.5","4R,0.5,4R,0.2,2B","8R2B,0.5","6R4B,0.2","5R,0.7")
# objects = ("Standard parameters", "Variable tx, reward values", "Low reward", "No reward", "No fee")
y_pos = np.arange(len(objects))
y_axis = [0,0,2,2,5,10,10,10,10]
# y_axis = [100,100,98,10,0]

plt.bar(y_pos, y_axis, align='center', alpha=1)
plt.xticks(y_pos, objects)
# plt.tick_params(axis='x', which='major', labelsize=5)

plt.ylabel("% of nodes in coalition")
# plt.ylabel("% of txs processed")
plt.xlabel('Rational node risk and composition')
plt.title('# of Coalition nodes with varying levels of risk')
# plt.title('Liveness of system under different parameters')
# plt.xlabel("Configuration used")
ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(10.0))
plt.savefig("BAR_bar_graph.png", dpi=100, bbox_inches="tight")
# plt.savefig("standard_bar_graph.png", dpi=100, bbox_inches="tight")
plt.show()