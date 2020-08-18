package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"strconv"
	"sync"
	"time"

	"go.etcd.io/etcd/clientv3"
	"go.etcd.io/etcd/etcdserver/api/v3rpc/rpctypes"
)

const (
	etcdPort = 2379 //client-facing port of each etcd node
	timeout  = 500 * time.Millisecond
)

/* put submits a put request to the etcd cluster and
* returns the start and end time, and if ok */
func put(cli *clientv3.Client, key, value string) (*time.Time, *time.Time, bool) {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	start := time.Now()
	_, err := cli.Put(ctx, key, value)
	if err != nil {
		switch err {
		case context.Canceled:
			// log.Fatalf("ctx is canceled by another routine: %v", err)
			return nil, nil, false
		case context.DeadlineExceeded:
			// log.Fatalf("ctx is attached with a deadline is exceeded: %v", err)
			return nil, nil, false
		case rpctypes.ErrEmptyKey:
			// log.Fatalf("client-side error: %v", err)
			return nil, nil, false
		default:
			// log.Fatalf("bad cluster endpoints, which are not etcd servers: %v", err)
			return nil, nil, false
		}
	}
	end := time.Now()
	return &start, &end, true
}

/* clientLoop is the main loop of each client thread */
func clientLoop(wg *sync.WaitGroup, endpoints []string, duration time.Duration, t0 time.Time, logger *log.Logger, id int) {
	defer wg.Done()
	cli, err := clientv3.New(clientv3.Config{
		Endpoints:   endpoints,
		DialTimeout: timeout,
	})
	if err != nil {
		logger.Printf("Error: client %d failed to connect to etcd cluster", id)
		return
	}
	go func() {
		seqNo := 0
		for true {
			start, end, ok := put(cli, fmt.Sprintf("#(%d,%d)", id, seqNo), "always the best")
			if !ok {
				logger.Printf("Error: client %d failed to commit request %d", id, seqNo)
			} else {
				logger.Printf("%d %d %d %d", id, seqNo, start.Sub(t0).Microseconds(), end.Sub(t0).Microseconds())
				seqNo++
			}
		}
	}()
	<-time.After(duration)
	return

}

/* run the main client threads
* logger is used to to serialize all prints to standard output */
func run(endpoints []string, numThreads int64, duration time.Duration, logger *log.Logger) {

	var wg sync.WaitGroup // wait for all threads to terminate
	t0 := time.Now()      // official start time of the experiment

	for i := 0; i < int(numThreads); i++ {
		wg.Add(1)
		go clientLoop(&wg, endpoints, duration, t0, logger, i)
	}
	wg.Wait()
	fmt.Println("Main: Completed")
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
	run(endpoints, numThreads, time.Duration(duration)*time.Second, logger)
}
