import multiprocessing
import time

def cpu_bound_task():
    count = 0
    for i in range(10 ** 7):
        count += 1
    return count


def process_task():
    result = cpu_bound_task()
    print(f"Task completed with count = {result}")


if __name__ == '__main__':
    start_time = time.time()

    # Creating 10 processes
    processes = []
    for _ in range(10):
        process = multiprocessing.Process(target=process_task)
        processes.append(process)
        process.start()

    # Waiting for all processes to complete
    for process in processes:
        process.join()

    print(f"Multiprocessing duration: {time.time() - start_time:.2f} seconds")