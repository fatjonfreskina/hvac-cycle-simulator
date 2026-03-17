from context import src
import unittest
import src.package_example.my_package_module as example_package
import src.example_module_1 as example_1

class DbTestSuite(unittest.TestCase):
    """Basic test cases."""

    # Simple unit test
    def test_example(self):
        assert True

    # test a package inside src/
    def test_package_function(self):
        assert example_package.package_function() == "Hello from package module"

    # Test functions in src/
    def test_main_module(self):
        assert example_1.example_function_1() == 1

if __name__ == '__main__':
    unittest.main()