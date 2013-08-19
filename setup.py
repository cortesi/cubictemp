from distutils.core import setup

long_description = """
A small, elegant templating system for Python.

Features
========

    * Simple, well-tested and well-documented.
    * Integrates tightly with Python - pass arbitrary Python objects into a
      template, walk sequences and iterators, evaluate expressions.
    * Default escaping helps to prevent common classes of Cross-Site Scripting
      vulnerabilities.
    * Encourages separation of interface and program logic by disallowing
      statements in templates.
    * Tiny - only ~ 170 SLOC. There are many large, over-designed
      Python templating systems out there.  Cubictemp proves that a templating
      sytem can be complete, elegant, powerful, fast and remain compact.

Cubictemp requires Python 2.4 or newer.
"""

setup(
        name="cubictemp",
        version="2.0",
        description="A more elegant templating library for a more civilised age",
        long_description=long_description,
        author="Aldo Cortesi",
        author_email="aldo@corte.si",
        license="MIT",
        py_modules = ["cubictemp"],
        classifiers = [
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Development Status :: 5 - Production/Stable",
            "Programming Language :: Python",
            "Operating System :: OS Independent",
            "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
            "Topic :: Software Development :: Libraries",
            "Topic :: Text Processing"
        ],
)
