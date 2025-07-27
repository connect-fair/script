from trigger_exploration import start_exploring
import threading

if __name__ == "__main__":
    # Number of threads you want to create
    num_threads = 2  # You can change this to your desired number
    # Create and start threads
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=start_exploring, args=("sakshi.knytt", "Bundilal@12345"))
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("All threads have finished execution")