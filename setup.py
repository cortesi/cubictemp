from distutils.core import setup

setup(
        name="cubictemp",
        version="2.0",
        description="A more elegant templating library for a more civilised age",
        author="Nullcube Pty Ltd",
        author_email="aldo@nullcube.com",
        license="MIT",
        url="http://dev.nullcube.com",
        download_url="http://dev.nullcube.com/download/cubictemp2.0.tar.gz",
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
        ]
)
