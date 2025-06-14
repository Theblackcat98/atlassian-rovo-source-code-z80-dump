"""Tests for code metrics calculations."""

from rovodev.modules.analytics.code_metrics import calculate_code_changes


def test_no_changes():
    """Test when content hasn't changed."""
    content = "line 1\nline 2\nline 3\n"
    metrics = calculate_code_changes(content, content)
    assert metrics["lines_added"] == 0
    assert metrics["lines_removed"] == 0


def test_add_single_line():
    """Test adding a single line."""
    original = "line 1\nline 2\n"
    modified = "line 1\nline 2\nline 3\n"
    metrics = calculate_code_changes(original, modified)
    assert metrics["lines_added"] == 1
    assert metrics["lines_removed"] == 0


def test_remove_single_line():
    """Test removing a single line."""
    original = "line 1\nline 2\nline 3\n"
    modified = "line 1\nline 3\n"
    metrics = calculate_code_changes(original, modified)
    assert metrics["lines_added"] == 0
    assert metrics["lines_removed"] == 1


def test_modify_single_line():
    """Test modifying a single line."""
    original = "line 1\nold line\nline 3\n"
    modified = "line 1\nnew line\nline 3\n"
    metrics = calculate_code_changes(original, modified)
    assert metrics["lines_added"] == 1
    assert metrics["lines_removed"] == 1


def test_multiple_changes():
    """Test multiple changes in different places."""
    original = "line 1\nline 2\nline 3\nline 4\n"
    modified = "line 1\nmodified 2\nline 3\nmodified 4\n"
    metrics = calculate_code_changes(original, modified)
    assert metrics["lines_added"] == 2
    assert metrics["lines_removed"] == 2


def test_empty_original():
    """Test when original content is empty."""
    original = ""
    modified = "line 1\nline 2\n"
    metrics = calculate_code_changes(original, modified)
    assert metrics["lines_added"] == 2
    assert metrics["lines_removed"] == 0


def test_empty_modified():
    """Test when modified content is empty."""
    original = "line 1\nline 2\n"
    modified = ""
    metrics = calculate_code_changes(original, modified)
    assert metrics["lines_added"] == 0
    assert metrics["lines_removed"] == 2


def test_both_empty():
    """Test when both contents are empty."""
    metrics = calculate_code_changes("", "")
    assert metrics["lines_added"] == 0
    assert metrics["lines_removed"] == 0


def test_whitespace_only_changes():
    """Test changes that only affect whitespace."""
    original = "line 1\n  line 2\nline 3\n"
    modified = "line 1\nline 2\nline 3\n"
    metrics = calculate_code_changes(original, modified)
    assert metrics["lines_added"] == 1
    assert metrics["lines_removed"] == 1


def test_newline_changes():
    """Test changes in line endings."""
    original = "line 1\nline 2\nline 3"  # No final newline
    modified = "line 1\nline 2\nline 3\n"  # With final newline
    metrics = calculate_code_changes(original, modified)
    assert metrics["lines_added"] == 1
    assert metrics["lines_removed"] == 1


def test_real_code_changes():
    """Test with real code-like content.

    The diff being tested:
    --- original
    +++ modified
    @@ -1,4 +1,5 @@
     def test():
    -    x = 1
    -    print("old")
    -    return x
    +    x = 2
    +    print("new")
    +    y = x + 1
    +    return y"""
    original = """def test():
    x = 1
    print("old")
    return x
"""
    modified = """def test():
    x = 2
    print("new")
    y = x + 1
    return y
"""
    metrics = calculate_code_changes(original, modified)
    assert metrics["lines_added"] == 4  # new value, new print, new y line, new return
    assert metrics["lines_removed"] == 3  # old value, old print, old return


def test_real_import_changes():
    """Test with real import changes.

    The diff being tested:
    --- original
    +++ modified
    @@ -1,4 +1,5 @@
    -from typing import Dict
    +from typing import Dict, List
     from pathlib import Path
    +from datetime import datetime

     def process(data: Dict) -> None:
         pass"""
    original = """from typing import Dict
from pathlib import Path

def process(data: Dict) -> None:
    pass"""
    modified = """from typing import Dict, List
from pathlib import Path
from datetime import datetime

def process(data: Dict) -> None:
    pass"""
    metrics = calculate_code_changes(original, modified)
    assert metrics["lines_added"] == 2  # modified import line, new import
    assert metrics["lines_removed"] == 1  # old import line


def test_real_function_changes():
    """Test with real function signature changes."""
    original = """def calculate_metrics(data):
    total = sum(data)
    return total"""
    modified = """def calculate_metrics(data: List[float]) -> float:
    # Calculate sum of numeric data
    total = sum(data)
    return total"""
    metrics = calculate_code_changes(original, modified)
    assert metrics["lines_added"] == 2  # new signature, new comment
    assert metrics["lines_removed"] == 1  # old signature


def test_real_class_changes():
    """Test with real class modifications.

    The diff being tested:
    --- original
    +++ modified
    @@ -1,3 +1,5 @@
     class User:
    +    \"\"\"User class with name.\"\"\"
     def __init__(self, name):
    -        self.name = name
    +        self.name = name
    +        self.active = True"""
    original = """class User:
    def __init__(self, name):
        self.name = name"""
    modified = """class User:
    \"\"\"User class with name.\"\"\"
    def __init__(self, name):
        self.name = name
        self.active = True"""
    metrics = calculate_code_changes(original, modified)
    assert metrics["lines_added"] == 3  # docstring, name (re-added due to indent), active
    assert metrics["lines_removed"] == 1  # name (old indent)


def test_real_decorator_changes():
    """Test with real decorator changes.

    The diff being tested:
    --- original
    +++ modified
    @@ -1,3 +1,7 @@
    +from functools import lru_cache
    +
    +@lru_cache(maxsize=100)
    +def process_data(data: int) -> int:
    +    \"\"\"Process data with caching.\"\"\"
    -def process_data(data):
         result = data * 2
         return result"""
    original = """def process_data(data):
    result = data * 2
    return result"""
    modified = """from functools import lru_cache

@lru_cache(maxsize=100)
def process_data(data: int) -> int:
    \"\"\"Process data with caching.\"\"\"
    result = data * 2
    return result"""
    metrics = calculate_code_changes(original, modified)
    assert metrics["lines_added"] == 5  # import, blank line, decorator, new signature, docstring
    assert metrics["lines_removed"] == 1  # old signature


def test_real_indentation_changes():
    """Test with real indentation level changes.

    The diff being tested:
    --- original
    +++ modified
    @@ -1,5 +1,6 @@
     def outer():
         if True:
             x = 1
    -        y = 2
    -        return x + y
    +        if x > 0:
    +            y = 2
    +            return x + y"""
    original = """def outer():
    if True:
        x = 1
        y = 2
        return x + y"""
    modified = """def outer():
    if True:
        x = 1
        if x > 0:
            y = 2
            return x + y"""
    metrics = calculate_code_changes(original, modified)
    assert metrics["lines_added"] == 3  # if condition, indented y, indented return
    assert metrics["lines_removed"] == 2  # old y, old return
