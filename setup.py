from setuptools import setup, find_packages

setup(
    name="minicompiler-lexer",
    version="0.1.0",
    description="Лексический анализатор для учебного компилятора MiniCompiler",
    author="Имя Разработчика",  # замените на своё имя
    author_email="email@example.com",  # замените на свой email
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "minicompiler = lexer.cli:main",  # команда после установки
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)