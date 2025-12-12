# Source: https://github.com/cython/cython/blob/master/Cython/Coverage.py
# Adapted from pysimdjson

"""
A coverage.py plugin that supports Cython.

This requires the coverage package to be installed.
"""

from __future__ import absolute_import

import os
import re
import sys
from collections import defaultdict

from coverage.plugin import CoveragePlugin, FileTracer, FileReporter
from coverage.files import abs_file, canonical_filename

try:
    from coverage.python import open_source_file
except ImportError:
    # older coverage versions
    def open_source_file(filename):
        return open(filename, 'r')

C_FILE_EXTENSIONS = {'.c', '.cpp', '.cc', '.cxx', '.c++'}


def is_package_dir(dir_path):
    for filename in ('__init__.py', '__init__.pyc', '__init__.pyo',
                     '__init__.pyd', '__init__.so'):
        if os.path.exists(os.path.join(dir_path, filename)):
            return True
    return False


def _find_dep_file_path(main_file, file_path, relative_path_search=False):
    """
    Find the absolute file path for a file path that refers to a dependency
    of the main_file.
    """
    if os.path.isabs(file_path):
        return abs_file(file_path)

    if relative_path_search:
        # Search relative to the main_file.
        # This is strictly somewhat incorrect, but is what a lot of people
        # assume. Use with caution.
        path = abs_file(os.path.join(os.path.dirname(main_file), file_path))
        if os.path.exists(path):
            return path

    # search in the package directories of the main_file
    # (checking "is_package_dir" is not entirely correct but huge optimisation)
    dir_path = os.path.dirname(main_file)
    while is_package_dir(dir_path):
        path = abs_file(os.path.join(dir_path, file_path))
        if os.path.exists(path):
            return path
        dir_path = os.path.dirname(dir_path)

    # fallback: search in the current directory and in sys.path
    if os.path.exists(file_path):
        return abs_file(file_path)

    for path in sys.path:
        path = os.path.join(path, file_path)
        if os.path.exists(path):
            return abs_file(path)

    return abs_file(file_path)


class Plugin(CoveragePlugin):
    def __init__(self, options=None):
        self._c_files_map = defaultdict(list)
        self._parsed_c_files = {}
        self._py_files_map = {}
        self._excluded_lines_map = {}
        self._excluded_line_patterns = None
        if options:
            self._excluded_line_patterns = options.get('exclude_lines')

    def file_tracer(self, filename):
        """
        Return a tracer for a file.
        """
        # Check for extension modules
        if filename.endswith('.so') or filename.endswith('.pyd'):
            return CythonModuleTracer(filename, self._py_files_map.get(filename), 
                                     c_file=None, c_files_map=self._c_files_map,
                                     file_path_map=self._py_files_map)
        
        # Check for source files directly (fallback if .so is not traced)
        if filename.endswith('.pyx'):
            abs_path = abs_file(filename)
            # Scan if we haven't mapped this yet
            # We don't have a module file (.so) to associate, but we can check if it's in our C files map
            found = False
            for mapped_source_file, (source_c_file, source_file, code) in self._c_files_map.items():
                if mapped_source_file == abs_path or source_file == filename:
                    found = True
                    break
            
            if not found:
                self._find_c_source_files(os.path.dirname(abs_path), abs_path)
            
            # Check again
            for mapped_source_file, (source_c_file, source_file, code) in self._c_files_map.items():
                if mapped_source_file == abs_path or source_file == filename:
                     # For .pyx files, we pass the C file as the "module_file" if we don't have the .so
                     # Or we can just return a tracer that relies on the map.
                     return CythonModuleTracer(source_c_file, filename, 
                                             c_file=source_c_file, c_files_map=self._c_files_map,
                                             file_path_map=self._py_files_map)
            
        return None

    def file_reporter(self, filename):
        """
        Return a reporter for a file.
        """
        # TODO: support .pxd files?
        _, ext = os.path.splitext(filename)
        if ext.lower() not in ('.pyx', '.pxi'):
            return None

        # Resolve to absolute path
        abs_path = abs_file(filename)

        # Check if we have seen this file in any of the C files we parsed
        for mapped_source_file, (source_c_file, source_file, code) in self._c_files_map.items():
            if mapped_source_file == abs_path or source_file == filename:
                return CythonModuleReporter(source_c_file, abs_path, filename, code,
                                          self._excluded_lines_map.get(abs_path))
        
        # If not found, try scanning the directory of the source file
        # This handles the case where coverage report is run separately and doesn't
        # have the state from coverage run
        self._find_c_source_files(os.path.dirname(abs_path), abs_path)

        # Check again after scanning
        for mapped_source_file, (source_c_file, source_file, code) in self._c_files_map.items():
            if mapped_source_file == abs_path or source_file == filename:
                return CythonModuleReporter(source_c_file, abs_path, filename, code,
                                          self._excluded_lines_map.get(abs_path))
            
        return None

    def find_executable_files(self, src_dir):
        """
        Yield all executable files in `src_dir`.
        """
        for root, dirs, files in os.walk(src_dir):
            for filename in files:
                if filename.endswith('.pyx') or filename.endswith('.pxi'):
                    path = os.path.join(root, filename)
                    yield path

    def _find_c_source_files(self, dir_path, source_file):
        """
        Desperately parse all C files in the directory or its package parents
        (not re-descending) to find the (included) source file in one of them.
        """
        if not os.path.isdir(dir_path):
            return

        splitext = os.path.splitext
        for filename in os.listdir(dir_path):
            ext = splitext(filename)[1].lower()
        for filename in os.listdir(dir_path):
            ext = splitext(filename)[1].lower()
            if ext in C_FILE_EXTENSIONS:
                self._read_source_lines(
                    os.path.join(dir_path, filename),
                    source_file
                )
                if source_file in self._c_files_map:
                    return

        # not found? then try one package up
        if is_package_dir(dir_path):
            self._find_c_source_files(os.path.dirname(dir_path), source_file)


    def _read_source_lines(self, c_file, sourcefile):
        """
        Parse a Cython generated C/C++ source file and find the executable
        lines.  Each executable line starts with a comment header that states
        source file and line number, as well as the surrounding range of source
        code lines.
        """
        if self._parsed_c_files is None:
            self._parsed_c_files = {}
        if c_file in self._parsed_c_files:
            code_lines = self._parsed_c_files[c_file]
        else:
            code_lines = self._parse_cfile_lines(c_file)
            self._parsed_c_files[c_file] = code_lines

        if self._c_files_map is None:
            self._c_files_map = {}

        for filename, code in code_lines.items():
            abs_path =_find_dep_file_path(c_file, filename,
                                           relative_path_search=True)
            # Support multiple C files mapping to the same source (unlikely but possible)
            # For now just overwrite or store one
            self._c_files_map[abs_path] = (c_file, filename, code)

        if sourcefile not in self._c_files_map:
            return (None,) * 2  # e.g. shared library file
        return self._c_files_map[sourcefile][1:]

    def _parse_cfile_lines(self, c_file):
        """
        Parse a C file and extract all source file lines that generated
        executable code.
        """
        match_source_path_line = re.compile(r' */[*] +"(.*)":([0-9]+)$').match
        match_current_code_line = re.compile(r' *[*] (.*) # <<<<<<+$').match
        match_comment_end = re.compile(r' *[*]/$').match
        match_trace_line = re.compile(r' *__Pyx_TraceLine\(([0-9]+),').match
        not_executable = re.compile(
            r'\s*c(?:type)?def\s+'
            r'(?:(?:public|external)\s+)?'
            r'(?:struct|union|enum|class)'
            r'(\s+[^:]+|)\s*:'
        ).match

        line_is_excluded = None
        if self._excluded_line_patterns:
            line_is_excluded = re.compile(
                '|'.join([
                    '(?:{0})'.format(regex)
                    for regex in self._excluded_line_patterns
                ])
            ).search

        code_lines = defaultdict(dict)
        executable_lines = defaultdict(set)
        current_filename = None

        if self._excluded_lines_map is None:
            self._excluded_lines_map = defaultdict(set)

        with open(c_file) as lines:
            lines = iter(lines)
            for line in lines:
                match = match_source_path_line(line)
                if not match:
                    if ('__Pyx_TraceLine(' in line and
                            current_filename is not None):
                        trace_line = match_trace_line(line)
                        if trace_line:
                            executable_lines[current_filename].add(
                                int(trace_line.group(1))
                            )
                    continue

                filename, lineno = match.groups()
                current_filename = filename
                lineno = int(lineno)
                for comment_line in lines:
                    match = match_current_code_line(comment_line)
                    if match:
                        code_line = match.group(1).rstrip()
                        if not_executable(code_line):
                            break
                        if (line_is_excluded is not None and
                                line_is_excluded(code_line)):
                            self._excluded_lines_map[filename].add(lineno)
                            break
                        code_lines[filename][lineno] = code_line
                        break
                    elif match_comment_end(comment_line):
                        # unexpected comment format - false positive?
                        break

        # Remove lines that generated code but are not traceable.
        for filename, lines in code_lines.items():
            dead_lines = set(lines).difference(
                executable_lines.get(filename, ())
            )
            for lineno in dead_lines:
                del lines[lineno]
        return code_lines


class CythonModuleTracer(FileTracer):
    """
    Find the Python/Cython source file for a Cython module.
    """
    def __init__(self, module_file, py_file, c_file, c_files_map,
                 file_path_map):
        super(CythonModuleTracer, self).__init__()
        self.module_file = module_file
        self.py_file = py_file
        self.c_file = c_file
        self._c_files_map = c_files_map
        self._file_path_map = file_path_map

    def has_dynamic_source_filename(self):
        return True

    def dynamic_source_filename(self, filename, frame):
        """
        Determine source file path.  Called by the function call tracer.
        """
        source_file = frame.f_code.co_filename
        try:
            return self._file_path_map[source_file]
        except KeyError:
            pass

        abs_path = _find_dep_file_path(filename, source_file)

        if self.py_file and source_file[-3:].lower() == '.py':
            # always let coverage.py handle this case itself
            self._file_path_map[source_file] = self.py_file
            return self.py_file

        assert self._c_files_map is not None
        # Lazy initialization
        if len(self._c_files_map) == 0: 
             # Just scan the src directory if map is empty
             # This is a hacky adaptation
             from coverage.plugin import Plugin
             # We need access to the plugin instance essentially, or just do the scan here
             # For now, let's just warn or skip
             pass

        if abs_path not in self._c_files_map:
            # Try to find it?
             pass
             
        self._file_path_map[source_file] = abs_path
        return abs_path


class CythonModuleReporter(FileReporter):
    """
    Provide detailed trace information for one source file to coverage.py.
    """
    def __init__(self, c_file, source_file, rel_file_path, code,
                 excluded_lines):
        super(CythonModuleReporter, self).__init__(source_file)
        self.name = rel_file_path
        self.c_file = c_file
        self._code = code
        self._excluded_lines = excluded_lines

    def lines(self):
        """
        Return set of line numbers that are possibly executable.
        """
        return set(self._code)

    def excluded_lines(self):
        """
        Return set of line numbers that are excluded from coverage.
        """
        return self._excluded_lines or set()

    def _iter_source_tokens(self):
        current_line = 1
        for line_no, code_line in sorted(self._code.items()):
            while line_no > current_line:
                yield []
                current_line += 1
            yield [('txt', code_line)]
            current_line += 1

    def source(self):
        """
        Return the source code of the file as a string.
        """
        if os.path.exists(self.filename):
            with open_source_file(self.filename) as f:
                return f.read()
        else:
            return '\n'.join(
                (tokens[0][1] if tokens else '')
                for tokens in self._iter_source_tokens())

    def source_token_lines(self):
        """
        Iterate over the source code tokens.
        """
        if os.path.exists(self.filename):
            with open_source_file(self.filename) as f:
                for line in f:
                    yield [('txt', line.rstrip('\n'))]
        else:
            for line in self._iter_source_tokens():
                yield [('txt', line)]


def coverage_init(reg, options):
    plugin = Plugin(options)
    reg.add_configurer(plugin)
    reg.add_file_tracer(plugin)
