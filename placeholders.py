#  Copyright 2023-2025 $author, All rights reserved.
#
#  For licensing terms, Please find the licensing terms in the closest
#  LICENSE.txt in this repository file going up the directory tree.
#

import re

placeholder_re: re.Pattern[str] = re.compile(r"(?P<indent>[ \t]+)?(?P<placeholder>\$\{(?P<name>[a-zA-Z0-9_]+?)(?P<options>:[a-z_,]+)*})")
space_re: re.Pattern[str] = re.compile(r"^[ \t]*$")
def apply_placeholders(template: str, check: bool = True, log: bool = False, **variables) -> str:
    """
    Replace placeholders in a template string with values from a dictionary
    :param template: The template string
    :param check: Whether to force a check for unfilled placeholders
    :param variables: The dictionary of values to replace
    :return: The template string with placeholders replaced
    :raises Exception: If check is True and there are unfilled placeholders

    >>> apply_placeholders("Hello, ${name}!", name="World")
    'Hello, World!'
    >>> apply_placeholders("Hello, ${name}!")
    Traceback (most recent call last):
    ...
    Exception: Template args not filled: name
    Defines: {}
    >>> apply_placeholders("Hello, ${name}!", check=False)
    'Hello, ${name}!'
    >>> apply_placeholders("  ${hello:keep_indent}", hello="Hello\\nWorld")
    '  Hello\\n  World'
    >>> apply_placeholders("  sometext\\n  ${hello}\\n  moretext", hello="")
    '  sometext\\n  \\n  moretext'
    >>> apply_placeholders("  sometext\\n  ${hello:no_empty_line}\\n  moretext", hello="")
    '  sometext\\n  moretext'
    >>> apply_placeholders("  ${hello:no_empty_line}", hello="")
    ''
    >>> apply_placeholders("  ${hello:no_empty_line}\\n  moretext", hello="")
    '  moretext'
    >>> apply_placeholders("  sometext\\n  ${hello:no_empty_line}", hello="")
    '  sometext\\n'
    >>> apply_placeholders("  ${hello:keep_indent,no_empty_line}", hello="")
    ''
    >>> apply_placeholders("  ${hello:keep_indent,no_empty_line}\\n  moretext", hello="")
    '  moretext'
    >>> apply_placeholders("  sometext\\n  ${hello:keep_indent,no_empty_line}", hello="")
    '  sometext\\n'
    >>> apply_placeholders("  ${hello:keep_indent,no_empty_line}", hello="hello\\nworld")
    '  hello\\n  world'
    >>> apply_placeholders("  ${hello:keep_indent,no_empty_line}\\n  moretext", hello="hello\\nworld")
    '  hello\\n  world\\n  moretext'
    >>> apply_placeholders("  sometext\\n  ${hello:keep_indent,no_empty_line}", hello="hello\\nworld")
    '  sometext\\n  hello\\n  world'
    """
    if log:
        print(f"--- Applying placeholders to template ---")
    replaced = True
    matched_variables = set()
    #while (matches := placeholder_re.finditer(template)) is not None and replaced:
    #    replaced = False
    #    for match in matches:
    while (match := placeholder_re.search(template)) is not None and replaced:
        replaced = False
        name: str = match.group("name")
        if name not in matched_variables:
            if (value := variables.get(name, None)) is not None:
                options = []
                value_lines = str(value).split("\n")
                placeholder = match.group("placeholder")
                while len(value_lines) > 0 and value_lines[0].strip() == "":
                    value_lines = value_lines[1:]
                while len(value_lines) > 0 and value_lines[-1].strip() == "":
                    value_lines = value_lines[:-1]
                if match.group("options"):
                    options = match.group("options")[1:].split(",")
                if "non_empty" in options and value == "":
                    raise Exception(f"Template arg '{name}' is empty")
                if "empty_no_line" in options and len(value_lines) == 0 or (len(value_lines) == 1 and value_lines[0].strip() == ""):
                    match_start = match.start("placeholder")
                    match_end = match.end("placeholder")
                    line_start = template.rfind("\n", 0, match_start - 1)
                    line_start = 0 if line_start == -1 else line_start + 1
                    line_end = template.find("\n", match_end)
                    line_end = len(template) if line_end == -1 else line_end
                    if space_re.match(template[line_start:match_start]) and space_re.match(template[match_end + 1:line_end]):
                        if log:
                            print(f"Removing empty line: '{template[line_start:line_end]}' for '{placeholder}'")
                        template = template[:line_start] + template[line_end + 1:]
                    else:
                        if log:
                            print(f"Replacing '{placeholder}' with empty")
                        template = template.replace(placeholder, "")
                else:
                    if "keep_indent" in options and len(value_lines) > 0 and (indent := match.group("indent")) is not None:
                        value_lines = [value_lines[0]] + [f"{indent}{line}" for line in value_lines[1:]]

                    value_str = "\n".join(value_lines)
                    if log:
                        print(f"Replacing '{placeholder}' with '{value_str}'")
                    template = template.replace(placeholder, value_str)
                matched_variables = set()
                replaced = True
            matched_variables.add(name)
    if check:
        match = placeholder_re.search(template)
        if match:
            raise Exception("Template args not filled: " + ", ".join(set([match.group("name") for match in placeholder_re.finditer(template)]))
                            + "\nDefines: " + str(variables) + "\nTemplate: " + template)

    return template

if __name__ == "__main__":
    import doctest
    doctest.testmod()

"""
NSTATIC mp_obj_t PyTIComponentInit(const mp_obj_type_t* type, size_t argCount, size_t, const mp_obj_t* args)N{N    auto* self = mp_obj_malloc(PyTIComponent, type);N    ${init_code:keep_indent,no_empty_line}N    return MP_OBJ_FROM_PTR(self);N}NSTATIC mp_obj_t PyMakeTIComponent(${namespace}TIComponent${template_args} value)N{N    return Tiny::Scripting::Utilities::ToPyType(value);N}NSTATIC void PyTIComponentAttr(mp_obj_t selfObj, qstr attr, mp_obj_t* dest)N{N    auto* self = static_cast<PyTIComponent*>(MP_OBJ_TO_PTR(selfObj));N    if (dest[0] == MP_OBJ_NULL)N    {N        ${attr_getters:keep_indent,no_empty_line}N        dest[1] = MP_OBJ_SENTINEL;N    }N    else if (dest[0] == MP_OBJ_SENTINEL)N    {N        if (dest[1] == MP_OBJ_NULL) { dest[0] = MP_OBJ_NULL; return; }N        ${attr_setters:keep_indent,no_empty_line}N    }N}NSTATIC mp_obj_t PyTIComponentUnaryOp(mp_unary_op_t op, mp_obj_t value)N{N    auto* self = static_cast<PyTIComponent*>(MP_OBJ_TO_PTR(value));N    switch (op)N    {N        case MP_UNARY_OP_BOOL: return self->Value ? mp_const_true : mp_const_false;N        ${unary_ops:keep_indent,no_empty_line}N        default: break;N    }N    return MP_OBJ_NULL;N}NSTATIC mp_obj_t PyTIComponentBinaryOp(mp_binary_op_t op, mp_obj_t lhs, mp_obj_t rhs)N{N    auto* self = static_cast<PyTIComponent*>(MP_OBJ_TO_PTR(lhs));N    switch (op)N    {N        ${binary_ops:keep_indent,no_empty_line}N        default: break;N    }N    return MP_OBJ_NULL;N}NSTATIC mp_obj_t PyTIComponentIndex(mp_obj_t self_in, mp_obj_t index, mp_obj_t value)N{N    auto* self = static_cast<PyTIComponent*>(MP_OBJ_TO_PTR(self_in));N    ${subscript_per_types:keep_indent,no_empty_line}N    return MP_OBJ_NULL;N}NSTATIC const mp_rom_map_elem_t PyTIComponentDictTable[] = {};NSTATIC MP_DEFINE_CONST_DICT(PyTIComponentDict, PyTIComponentDictTable);NMP_DEFINE_CONST_OBJ_TYPE(PyTIComponentType, MP_QSTR_${py_type_name}, MP_TYPE_FLAG_NONE, make_new, PyTIComponentInit,N                         locals_dict, PyTIComponentDict, attr, PyTIComponentAttr, subscr, PyTIComponentIndex,N                         unary_op, PyTIComponentUnaryOp, binary_op, PyTIComponentBinaryOp);N
"""