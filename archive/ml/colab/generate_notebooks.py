import json
from typing import Dict, Any, List


def create_notebook(cells: List[Dict[str, Any]]) -> str:
    nb = {
        "cells": cells,
        "metadata": {
            "colab": {"provenance": []},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
            "accelerator": "GPU"
        },
        "nbformat": 4,
        "nbformat_minor": 0
    }
    return json.dumps(nb, indent=2)


def code_cell(code: str) -> Dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in code.split("\n")]
    }


def md_cell(markdown: str) -> Dict[str, Any]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in markdown.split("\n")]
    }
