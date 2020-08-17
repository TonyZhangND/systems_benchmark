package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"strconv"
	"time"

	"go.etcd.io/etcd/clientv3"
	"go.etcd.io/etcd/etcdserver/api/v3rpc/rpctypes"
)

const (
	etcdPort = 2379 //client-facing port of each etcd node
	timeout  = 5 * time.Second
)

/* put submits a put request to the etcd cluster and
* returns the latency in microseconds, and if ok */
func put(cli *clientv3.Client, key, value string) (int64, bool) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	start := time.Now()
	_, err := cli.Put(ctx, key, value)
	if err != nil {
		switch err {
		case context.Canceled:
			// log.Fatalf("ctx is canceled by another routine: %v", err)
			return -1, false
		case context.DeadlineExceeded:
			// log.Fatalf("ctx is attached with a deadline is exceeded: %v", err)
			return -1, false
		case rpctypes.ErrEmptyKey:
			// log.Fatalf("client-side error: %v", err)
			return -1, false
		default:
			// log.Fatalf("bad cluster endpoints, which are not etcd servers: %v", err)
			return -1, false
		}
	}
	end := time.Now()
	elapsed := end.Sub(start)
	return elapsed.Microseconds(), true
}

/* run the main client threads
* logger is used to to serialize all prints to standard output */
func run(endpoints []string, numThreads int64, duration int64, logger *log.Logger) {
	cli, err := clientv3.New(clientv3.Config{
		Endpoints:   endpoints,
		DialTimeout: 5 * time.Second,
	})
	if err != nil {
		// handle error!
	}
	elapsed, ok := put(cli, "tony", "always the best")
	if !ok {
		logger.Printf("Error")
	} else {
		logger.Printf("%d", elapsed)
	}
}

/* main function.
*  This program takes the following positional arguments
* <node1 ip> <node2 ip> ... <num_threads> <duration_secs> */
func main() {
	if len(os.Args) < 4 {
		fmt.Printf("Usage: <node1 ip> <node2 ip> ... <num_threads> <duration_secs>\n")
		os.Exit(1)
	}

	// Grab the third-to-last argument from os.Args -- that is num_threads
	var numThreads, err1 = strconv.ParseInt(os.Args[len(os.Args)-2], 10, 64)
	if int(numThreads) < 1 || err1 != nil {
		fmt.Printf("Error: Invalid number of threads %v\n", os.Args[len(os.Args)-2])
		os.Exit(1)
	}

	// Grab the second-to-last argument from os.Args -- that is duration
	var duration, err2 = strconv.ParseInt(os.Args[len(os.Args)-1], 10, 64)
	if int(duration) < 1 || err2 != nil {
		fmt.Printf("Error: Invalid duration %v\n", os.Args[len(os.Args)-1])
		os.Exit(1)
	}

	var endpoints = make([]string, len(os.Args)-2)
	for i := 0; i < len(endpoints); i++ {
		endpoints[i] = fmt.Sprintf("%s:%d", os.Args[i+1], etcdPort)
	}

	// use a logger to serialize all prints to standard output
	var logger = log.New(os.Stdout,
		"REQUEST: ", log.LstdFlags)
	run(endpoints, numThreads, duration, logger)
}
