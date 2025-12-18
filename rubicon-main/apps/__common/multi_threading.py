import time
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_in_threads_single_function(target_func, kwargs_list):
    results = [None] * len(kwargs_list)
    with ThreadPoolExecutor() as executor:
        future_to_index = {}
        for i, kwargs in enumerate(kwargs_list):
            kwargs_copy = kwargs.copy()
            args = kwargs_copy.pop('args', ())
            future = executor.submit(target_func, *args, **kwargs_copy)
            future_to_index[future] = i
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            results[index] = future.result()
    return results

###########################################################################################

def run_function(func, args, kwages):
    return func(*args, **kwages)

def run_in_threads_multi_function(functions):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_function, func, args, kwargs) for func, args, kwargs in functions]

        results = [future.result() for future in futures]
        return results


if __name__ == "__main__":
    # Define example functions that accept multiple arguments
    def function_1(arg1, arg2):
        print(f"Function 1 is running with arguments: {arg1}, {arg2}")
        time.sleep(3)  # Simulate some delay
        return f"Function 1 result: {arg1}, {arg2}"

    def function_2(arg1, arg2, arg3):
        print(f"Function 2 is running with arguments: {arg1}, {arg2}, {arg3}")
        time.sleep(2)  # Simulate some delay
        return f"Function 2 result: {arg1}, {arg2}, {arg3}"

    def function_3(arg1):
        print(f"Function 3 is running with argument: {arg1}")
        time.sleep(2)  # Simulate some delay
        return f"Function 3 result: {arg1}"

    # List of functions and their corresponding arguments
    functions = [
        (function_1, ('arg1_func1', 'arg2_func1'), {}),
        (function_2, ('arg1_func2', 'arg2_func2', 'arg3_func2'), {}),
        (function_3, ('arg1_func3',), {}),
    ]

    results = run_in_threads_multi_function(functions)
    print("Results:", results)


    def compute_square(base, exponent):
        # time.sleep(exponent)
        return base ** exponent


    kwargs_list = [
        {'args': (2, 3)},       # 2^3
        {'args': (3, 2)},       # 3^2
        {'args': (4, 1)},       # 4^1
        {'args': (5, 0)}        # 5^0
    ]

    results = run_in_threads_single_function(target_func=compute_square, kwargs_list=kwargs_list)
    print("Results:", results)

##################################################################################################################
##################################################################################################################