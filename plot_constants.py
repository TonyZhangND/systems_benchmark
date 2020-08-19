import matplotlib.pyplot as plt

# Global plotting params
# Fonts
base_size = 7
plt.rc('font', family='sans-serif') 
plt.rc('font', size=base_size)              # controls default text sizes
plt.rc('axes', titlesize=base_size)        # fontsize of the axes title
plt.rc('axes', labelsize=base_size)        # fontsize of the x and y labels
plt.rc('xtick', labelsize=base_size)       # fontsize of the tick labels
plt.rc('ytick', labelsize=base_size)       # fontsize of the tick labels
plt.rc('legend', fontsize=base_size)       # legend fontsize
# plt.rc('figure', titlesize=12)      # fontsize of the figure title

# Graphics
plt.rc('lines', linewidth=0.7)
plt.rc('lines', markersize=2.1)
plt.rc('legend', frameon=False)        # No frame around legend
plt.rc('axes', linewidth=0.5)
# plt.rcParams['xtick.major.size'] = 2
plt.rcParams['xtick.major.width'] = 0.5
plt.rcParams['xtick.minor.width'] = 0.5
# plt.rcParams['ytick.major.size'] = 2
plt.rcParams['ytick.major.width'] = 0.5
plt.rcParams['ytick.minor.width'] = 0.5
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'


# Figure size
fig_width = 3.4
fig_height = 5