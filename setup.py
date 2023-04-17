import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='mcpt-torch',
    version='0.6',
    author='NKCS MCPT Team',
    author_email='zyzhong@mail.nankai.edu.cn',
    description='Implementation of MCPT in PyTorch',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/alumik/mcpt-torch',
    packages=setuptools.find_packages(include=['mcpt', 'mcpt.*']),
    platforms='any',
    install_requires=[
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.6,<3.12',
)
