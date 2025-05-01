from setuptools import setup, find_packages

setup(
    name="local-ai-utils-embedding",
    version="0.0.1",
    packages=['embedding'],
    package_dir={"embedding": "embedding"},
    entry_points={
        'console_scripts': [
            'embedding=embedding.cli:main',
        ],
    },
    install_requires=[
        'lancedb',
        'fire',
        'numpy',
        'platformdirs',
        'pyarrow'
    ],
)