#  Copyright 2023-2025 $author, All rights reserved.
#
#  For licensing terms, Please find the licensing terms in the closest
#  LICENSE.txt in this repository file going up the directory tree.
#

import os
import sys
import re
from dataclasses import dataclass
from typing import Iterable, Optional

from .placeholders import apply_placeholders

# We only support a subset of preprocessor commands to avoid having to perform full C++ parsing and evaluation.
if_preprocessor_re: re.Pattern[str] = re.compile(r"\s*#if\s+.*")
ifdef_preprocessor_re: re.Pattern[str] = re.compile(r"\s*#ifdef\s+(?P<name>[a-zA-Z0-9_]+).*")
ifndef_preprocessor_re: re.Pattern[str] = re.compile(r"\s*#ifndef\s+(?P<name>[a-zA-Z0-9_]+).*")
else_preprocessor_re: re.Pattern[str] = re.compile(r"\s*#else")
endif_preprocessor_re: re.Pattern[str] = re.compile(r"\s*#endif")
comment_parser_re: re.Pattern[str] = re.compile(r"\s*(?P<line>.*)\s*.*$")
empty_line_re: re.Pattern[str] = re.compile(r"^\s*$")
define_re: re.Pattern[str] = re.compile(r"\s*#define\s+(?P<name>[a-zA-Z0-9_]+)\s+(?P<value>.*)")
remove_block_comment_re: re.Pattern[str] = re.compile(r"^(?P<pre_code>.*?)(?P<opencomment>/\*)?.*?(?P<closecomment>\*/)?(?P<post_code>.*)$")

def filter_code(input: Iterable[str], **defines) -> Iterable[str]:
    in_comment = False
    preprocessor_stack: list[Optional[tuple[Optional[str], bool, bool]]] = []
    def _in_false_preprocessor() -> bool:
        for define, negate, in_else in preprocessor_stack:
            if define is not None:
                if in_else:
                    negate = not negate

                is_defined = define in defines
                if is_defined == negate:
                    return True
        return False
    for line_index, line in enumerate(input):
        if match := comment_parser_re.match(line):
            line = match.group("line")
        if empty_line_re.match(line):
            continue

        while match := remove_block_comment_re.match(line):
            line = f"{match.group('pre_code')} {match.group('post_code')}"
            if match.group("opencomment") is not None:
                in_comment |= True
            if match.group("closecomment") is not None:
                in_comment = False
            if match.group("opencomment") is None and match.group("closecomment") is None:
                break

        if if_preprocessor_re.match(line):
            preprocessor_stack.append((None, False, False))
            continue
        if match := ifdef_preprocessor_re.match(line):
            preprocessor_stack.append((match.group("name"), False, False))
            continue
        elif match := ifndef_preprocessor_re.match(line):
            preprocessor_stack.append((match.group("name"), True, False))
            continue
        elif else_preprocessor_re.match(line):
            current_define, negate, in_else = preprocessor_stack.pop()
            preprocessor_stack.append((current_define, negate, True))
            continue
        elif endif_preprocessor_re.match(line):
            preprocessor_stack.pop()
            continue

        if _in_false_preprocessor() or in_comment:
            continue

        if match := define_re.match(line):
            defines[match.group("name")] = match.group("value")

        yield line.strip()

@dataclass
class CompilerArgs:
    files: list[str]
    defines: dict[str, str]
    header_paths: list[str]
    library_paths: list[str]
    libraries: list[str]
    warnings: list[str]
    flags: list[str]
    compiler_args: list[str]
    def __init__(self):
        self.files = []
        self.defines = {}
        self.header_paths = []
        self.library_paths = []
        self.libraries = []
        self.warnings = []
        self.flags = []
        self.compiler_args = []

def parse_compiler_args(compiler_args: list[str]) -> CompilerArgs:
    args = CompilerArgs()
    current_prefix = None
    in_args = list(compiler_args)
    while len(in_args) > 0:
        arg = in_args.pop(0).strip()
        if arg.startswith("\"") and arg.endswith("\""):
            arg = arg[1:-1]
        if arg.startswith("-D"):
            key_value = arg[2:].split("=", 1)
            if len(key_value) < 2:
                args.defines[key_value[0]] = ""
            else:
                args.defines[key_value[0]] = key_value[1]
        elif arg.startswith("-iprefix"):
            arg = arg[8:]
            if len(arg.strip()) < 1:
                arg = in_args.pop(0)
            if arg.startswith("\"") and arg.endswith("\""):
                arg = arg[1:-1]
            current_prefix = arg
        elif arg.startswith("-iwithprefixbefore"):
            if current_prefix is None:
                raise ValueError("No prefix specified for -iwithprefixbefore")
            arg = arg[18:]
            if len(arg.strip()) < 1:
                arg = in_args.pop(0)
            if arg.startswith("\"") and arg.endswith("\""):
                arg = arg[1:-1]
            args.header_paths.append(os.path.join(current_prefix, arg))
        elif arg.startswith("-I"):
            args.header_paths.append(arg[2:])
        elif arg.startswith("-L"):
            args.library_paths.append(arg[2:])
        elif arg.startswith("-l"):
            args.libraries.append(arg[2:])
        elif arg.startswith("-W"):
            args.warnings.append(arg[2:])
        elif arg.startswith("-f"):
            args.flags.append(arg)
        elif arg.startswith("-"):
            args.compiler_args.append(arg)
        else:
            args.files.append(arg)

    args.defines = {key: apply_placeholders(value, **args.defines) for key, value in args.defines.items()}
    args.header_paths = [apply_placeholders(path, **args.defines) for path in args.header_paths]
    args.library_paths = [apply_placeholders(path, **args.defines) for path in args.library_paths]

    return args

if __name__ == "__main__":
    import doctest
    doctest.testmod()
