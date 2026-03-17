from setuptools import setup, find_packages

with open("README", 'r') as f:
    long_description = f.read()

setup(
    name = 'template-name',
    version='1.0',
    description= 'Descrizione',
    long_description=long_description,
    author= 'Fatjon Freskina', 
    author_email='fatjon.developer@gmail.com',
    packages = find_packages(),
    )