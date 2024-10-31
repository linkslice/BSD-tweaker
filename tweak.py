import subprocess
import re
import argparse
import time
import os

# Store original sysctl values for reverting
original_values = {}

def run_command(command):
    """Run a shell command and return the output as a string."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def set_sysctl(name, value):
    """Set a sysctl variable and confirm the change."""
    command = f"sysctl -w {name}={value}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(f"Setting {name} to {value}: {'Success' if result.returncode == 0 else 'Failed'}")

def get_sysctl(name):
    """Get the current value of a sysctl variable."""
    return run_command(f"sysctl -n {name}")

def save_sysctl(name, value):
    """Save a sysctl variable to /etc/sysctl.conf for persistence."""
    with open("/etc/sysctl.conf", "a") as conf:
        conf.write(f"{name}={value}\n")

def revert_sysctl(name):
    """Revert sysctl to its original value, if recorded."""
    if name in original_values:
        set_sysctl(name, original_values[name])

def get_cpu_info():
    """Get CPU model and number of cores."""
    model = get_sysctl("hw.model")
    cores = int(get_sysctl("hw.ncpu"))
    smt = get_sysctl("hw.smt")
    return model, cores, smt

def get_memory_info():
    """Get physical and user memory."""
    physmem = int(get_sysctl("hw.physmem")) // (1024 ** 2)  # Convert to MB
    usermem = int(get_sysctl("hw.usermem")) // (1024 ** 2)  # Convert to MB
    return physmem, usermem

def get_network_settings():
    """Retrieve network-related sysctl settings."""
    tcp_sendspace = int(get_sysctl("net.inet.tcp.sendspace"))
    tcp_recvspace = int(get_sysctl("net.inet.tcp.recvspace"))
    return tcp_sendspace, tcp_recvspace

def cpu_benchmark():
    """Simple CPU-intensive benchmark."""
    start_time = time.time()
    for _ in range(1000000):
        _ = 3.14159 ** 2
    return time.time() - start_time

def memory_benchmark():
    """Simple memory read/write benchmark."""
    start_time = time.time()
    data = [0] * 10000000  # Allocate a large list of zeros
    for i in range(len(data)):
        data[i] = i % 256  # Modify list to simulate memory usage
    return time.time() - start_time

def network_benchmark():
    """Simulate network performance by testing data manipulation."""
    start_time = time.time()
    data = b"x" * 1000000
    _ = data.replace(b"x", b"y")  # Simulate simple network data handling
    return time.time() - start_time

def benchmark_system():
    """Run benchmarks and return results as a dictionary."""
    cpu_time = cpu_benchmark()
    memory_time = memory_benchmark()
    network_time = network_benchmark()
    return {
        "CPU Benchmark Time (s)": cpu_time,
        "Memory Benchmark Time (s)": memory_time,
        "Network Benchmark Time (s)": network_time
    }

def suggest_tweaks(cpu_info, memory_info, network_settings, try_flag=False, keep_flag=False):
    """Suggest sysctl tuning parameters and optionally apply them."""
    model, cores, smt = cpu_info
    physmem, usermem = memory_info
    tcp_sendspace, tcp_recvspace = network_settings

    recommendations = []

    # CPU-related recommendations
    if cores > 2:
        recommendations.append(("kern.sched.quantum", 10))  # Increase quantum for better multi-core scheduling
    if smt == '1':
        recommendations.append(("hw.smt", 0))  # Disable SMT for security on multi-core systems

    # Memory-related recommendations
    if physmem >= 4096:
        recommendations.append(("kern.maxvnodes", 250000))  # Higher vnode cache for systems with more memory
    else:
        recommendations.append(("kern.bufcachepercent", 15))  # Lower buffer cache if memory is limited

    # Network-related recommendations
    if tcp_sendspace < 65536:
        recommendations.append(("net.inet.tcp.sendspace", 65536))  # Increase send space
    if tcp_recvspace < 65536:
        recommendations.append(("net.inet.tcp.recvspace", 65536))  # Increase receive space

    # General tuning
    recommendations.append(("kern.somaxconn", 1024))  # Increase max connection backlog

    # Display and optionally apply recommendations
    print("\nRecommended sysctl tweaks and performance suggestions:")
    for sysctl_name, suggested_value in recommendations:
        current_value = get_sysctl(sysctl_name)
        print(f"- {sysctl_name}: Current = {current_value}, Suggested = {suggested_value}")
        if try_flag:
            # Record original values for reversion
            if sysctl_name not in original_values:
                original_values[sysctl_name] = current_value
            # Apply sysctl tweak
            set_sysctl(sysctl_name, suggested_value)
            if keep_flag:
                save_sysctl(sysctl_name, suggested_value)

def main():
    # Set up argument parser for the --try, --keep, and --revert flags
    parser = argparse.ArgumentParser(description="Suggest and optionally apply sysctl tweaks for OpenBSD.")
    parser.add_argument('--try', action='store_true', help="Apply suggested sysctl tweaks directly and compare benchmarks")
    parser.add_argument('--keep', action='store_true', help="Save applied sysctl tweaks to /etc/sysctl.conf for persistence")
    parser.add_argument('--revert', action='store_true', help="Revert sysctl settings to original values")
    args = parser.parse_args()

    # Gather information
    cpu_info = get_cpu_info()
    memory_info = get_memory_info()
    network_settings = get_network_settings()

    # Display gathered info
    print(f"CPU Model: {cpu_info[0]}, Cores: {cpu_info[1]}, SMT Enabled: {cpu_info[2]}")
    print(f"Physical Memory: {memory_info[0]} MB, User Memory: {memory_info[1]} MB")
    print(f"TCP Send Space: {network_settings[0]}, TCP Receive Space: {network_settings[1]}")

    # Benchmark before applying tweaks
    if args.try:
        print("\nRunning benchmarks before applying tweaks...")
        pre_benchmarks = benchmark_system()
        for key, value in pre_benchmarks.items():
            print(f"{key}: {value:.4f} seconds")

    if args.revert:
        # Revert sysctl settings to their original values
        print("\nReverting sysctl settings to original values...")
        for sysctl_name in original_values.keys():
            revert_sysctl(sysctl_name)

    else:
        # Generate and display/apply recommendations
        suggest_tweaks(cpu_info, memory_info, network_settings, try_flag=args.try, keep_flag=args.keep)

        # Benchmark after applying tweaks
        if args.try:
            print("\nRunning benchmarks after applying tweaks...")
            post_benchmarks = benchmark_system()
            for key, value in post_benchmarks.items():
                print(f"{key}: {value:.4f} seconds")

            # Show comparison
            print("\nPerformance comparison (before vs after):")
            for key in pre_benchmarks.keys():
                pre_time = pre_benchmarks[key]
                post_time = post_benchmarks[key]
                improvement = pre_time - post_time
                print(f"{key}: {pre_time:.4f} -> {post_time:.4f} seconds (Improvement: {improvement:.4f} seconds)")

if __name__ == "__main__":
    main()
