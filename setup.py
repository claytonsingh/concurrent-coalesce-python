from setuptools import setup, find_packages
import toml

with open("pyproject.toml", "r") as f:
    pyproject = toml.load(f)
    project = pyproject["project"]

setup(
    name=project["name"],
    version=project["version"],
    description=project["description"],
    long_description=open(project["readme"], "r").read(),
    long_description_content_type="text/markdown",
    author=project["authors"][0]["name"],
    author_email=project["authors"][0]["email"],
    python_requires=project["requires-python"],
    install_requires=project["dependencies"],
    packages=find_packages(),
    classifiers=project["classifiers"],
    keywords=project["keywords"],
    license=project["license"]["text"],
    url=project["urls"]["Homepage"],
    project_urls=project["urls"],
)
