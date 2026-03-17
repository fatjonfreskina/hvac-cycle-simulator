from example_module_1 import *
from package_example import my_package_module

def main() -> None:

    print(f"Output from example_module: {example_function_1()}")
    print(my_package_module.package_function())

if __name__ == "__main__":
    main()