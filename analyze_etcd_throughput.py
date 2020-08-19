import sys
import os
import csv
import statistics
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
import pickle

from plot_constants import *

def main(exp_dir):
    exp_dir = os.path.abspath(exp_dir)
    print("\nAnalyzing data for experiment %s" %exp_dir)

    # total_data is dict (f -> threads -> trials -> [ (start, end, client_id)... ]
    total_data = parse_batch_files(exp_dir)

    name = "latency_throughput"
    gen_graphs(name, exp_dir, total_data)


def parse_batch_files(exp_dir):
    """Collects the total data for the experiment

    Arguments:
        exp_dir {string} -- root directory of experiment
    Returns:
        dict (f -> threads -> trial_num -> [ latencies ... ]
    """
    # total_data is dict (f -> threads -> trials -> [ (start, end, client_id)... ]
    total_data = dict()
    for root, _, files in os.walk(exp_dir):
        files = [f for f in files if not f[0] == '.']  # ignore hidden files
        if files != [] and 'threads' in root:
            # This is a leaf directory containing trial csv files
            
            trial_files = [f for f in files if "skynode" not in f]
            for file in trial_files:
                full_path = "%s/%s" %(root, file)
                f, num_threads, trial_num = parse_trial_params(full_path)
                # Populate the dict
                if f not in total_data:
                    total_data[f] = dict()
                if num_threads not in total_data[f]:
                    total_data[f][num_threads] = dict()
                total_data[f][num_threads][trial_num] = parse_client_log(full_path)
    return total_data


def gen_graphs(name, root, total_data):
    """Plots the latency throughput graph in one pdf file

    Arguments:
        name {string} -- name of this file
        root -- directory to save this figure
        total_data {dict} -- (f -> threads -> trials -> [ (start, end, client_id)... ]
    """
    with PdfPages("%s/%s.pdf" %(root, name)) as pp:
        fig, axes = plt.subplots(len(total_data)*2, 1, figsize=(fig_width, fig_height), sharex=False)
        fig.subplots_adjust(left=0.14, right=0.95, top=0.92, bottom=0.1, hspace=0.3)
        row = 0
        for f in sorted(list(total_data.keys())):
            latencies = compute_average_latencies(total_data[f])
            throughputs = compute_average_throughputs(total_data[f])
            print("Latency (ms): ", latencies)
            print("Throughput (req/s): ", throughputs)
            plot_latency_throughput(axes[row], "etcd latency and throughput, f=%d" %f, latencies, throughputs)
            row += 1
            plot_littles_law(axes[row], "etcd little's law, f=%d" %f, latencies, throughputs)
            row += 1
        pp.savefig(fig)
        plt.close(fig)


def plot_littles_law(this_ax, title, latencies, throughputs):
    this_ax.set_title(title)
    this_ax.set_xlabel("number of clients")
    this_ax.set_ylabel("throughput")

    num_clients = [2**i for i in range(len(latencies))]
    predicted_throughputs = [num_clients[i]/latencies[i]*1000 for i in range(len(num_clients))]
    this_ax.plot(num_clients, throughputs, marker='x',  label="observed", color='navy')
    this_ax.plot(num_clients, predicted_throughputs, marker='x',  label="predicted", color='green')
    this_ax.legend()


def plot_latency_throughput(this_ax, title, latencies, throughputs):
    this_ax.set_title(title)
    this_ax.set_xlabel("throughput (reqs/sec)")
    this_ax.set_ylabel("request latency (ms)")
    # this_ax.grid()
    # stats = AnchoredText(
    #         generate_statistics(latencies, throughputs), 
    #         loc='upper right',  
    #         prop=dict(size=8),
    #         bbox_to_anchor=(1.1, 1),
    #         bbox_transform=this_ax.transAxes
    #         )
    # # this_ax.add_artist(stats)
    this_ax.plot(throughputs, latencies, marker='x',  label="observed performance", color='navy')
    for i in range(len(throughputs)):
        this_ax.annotate("%d" %(2**i), (throughputs[i], latencies[i]))
    this_ax.legend()
    


def generate_statistics(latencies, throughputs):
    """
    Generates a string containing some statistics for the input
    Arguments:
        input -- list of numbers
    """
    res = []
    res.append("min latency = %.3f" %(min(latencies)))
    res.append("max throughput = %.3f" %(max(throughputs)))
    return "\n".join(res)


def compute_average_throughputs(total_f_data):
    """Computes the average throughputs for each num_threads for this f

    Arguments:
        total_f_data {dict} -- (threads -> trials -> [ (start, end, client_id)... ]
    returns
        {list} -- throughputs list
    """
    res = []
    for num_threads in sorted(list(total_f_data.keys())):
        avg_trial_throughputs = []  # list of average tp for each trial
        for trial in sorted(list(total_f_data[num_threads].keys())): 
            trial_data = total_f_data[num_threads][trial]

            trial_start_time = min([start for (start, end, client_id) in trial_data])
            trial_end_time = max([end for (start, end, client_id) in trial_data])
            num_requests = len(trial_data)
            avg_trial_throughputs.append(float(num_requests)/(trial_end_time-trial_start_time)*1000_000.0) # this is in req/s
        res.append(np.mean(avg_trial_throughputs))
    return res


def compute_average_latencies(total_f_data):
    """Computes the average latencies for each num_threads for this f

    Arguments:
        total_f_data {dict} -- (threads -> trials -> [ (start, end, client_id)... ]
    returns
        {list} -- latencies list
    """
    res = []
    for num_threads in sorted(list(total_f_data.keys())):
        avg_trial_latencies = []  # list of average latency for each trial
        for trial in sorted(list(total_f_data[num_threads].keys())): 
            trial_latencies = []  # list of all latency for this trial
            trial_data = total_f_data[num_threads][trial]
            for req in trial_data:
                trial_latencies.append((req[1]-req[0])/1000) # this is in ms
            avg_trial_latencies.append(np.mean(trial_latencies))
        res.append(np.mean(avg_trial_latencies))
    return res


def parse_trial_params(path):
    """Returns the trial params given the path string
    Arguments:
        path {string} -- full path to this trial log
    Returns:
        {int} -- f
        {int} -- num theads
        {int} -- trial number
    """
    segments = path.split('/')
    f = int(segments[-3].split('_')[1])
    num_threads = int(segments[-2].split('_')[1])
    trial_num = int(segments[-1].split('ial')[1].split(".")[0])
    return f, num_threads, trial_num


def parse_client_log(client_log):
    """Parses the client log into the format
    [ (start, end, client_id)... ]
    Arguments:
        client_log {string} -- path to a client log
    Returns:
        {list} -- [ (start, end, client_id)... ]
    """
    res = []
    with open(client_log, 'r') as client:
        csvreader = csv.reader(client, delimiter=' ')
        for row in csvreader:
            if len(row) < 4:
                continue
            if 'Error' in row[3]:
                continue
            start = int(row[5])
            end = int(row[6])
            client_id = int(row[3])
            res.append((start, end, client_id))
    # Ignore the first and last 20%
    num_reqs = len(res)
    truncated_res = []
    for i in range(num_reqs):
        if i > num_reqs * 0.2 and i < num_reqs * 0.8:
            truncated_res.append(res[i])
    return truncated_res


if __name__ == "__main__":
    # positional arguments <experiment_dir>
    # experiment_dir is something like /home/nudzhang/Documents/littles-law-benchmarking/etcd/data/18-Aug-1435
    exp_dir =sys.argv[1]
    main(exp_dir)