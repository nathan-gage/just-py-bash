from __future__ import annotations

from just_bash import (
    get_command_names,
    get_javascript_command_names,
    get_network_command_names,
    get_python_command_names,
    parse,
    serialize,
)

script = "echo hello | grep h && printf 'done\\n'"
ast = parse(script)
statements = ast.get("statements")
statement_count = len(statements) if isinstance(statements, list) else 0

print("=== Command registry helpers ===")
print(f"builtins include echo={'echo' in get_command_names()}")
print(f"network commands={get_network_command_names()}")
print(f"python commands={sorted(get_python_command_names())}")
print(f"javascript commands={sorted(get_javascript_command_names())}")

print("=== Parser helpers ===")
print(f"ast.type={ast['type']}")
print(f"statement_count={statement_count}")
print(f"serialized={serialize(ast)}")
