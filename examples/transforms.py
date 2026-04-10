from __future__ import annotations

from datetime import UTC, datetime

from just_bash import Bash, BashTransformPipeline, CommandCollectorPlugin, TeePlugin

script = "echo hello | grep h"
timestamp = datetime(2024, 1, 15, 10, 30, 45, 123000, tzinfo=UTC)

print("=== Standalone transform pipeline ===")
pipeline_result = (
    BashTransformPipeline()
    .use(TeePlugin(output_dir="/tmp/logs", timestamp=timestamp))
    .use(CommandCollectorPlugin())
    .transform(script)
)
print(pipeline_result.script)
print(pipeline_result.metadata)

print("=== Session-integrated transform plugins ===")
with Bash() as bash:
    bash.register_transform_plugin(CommandCollectorPlugin())
    transformed = bash.transform(script)
    exec_result = bash.exec(script)

print(transformed.metadata)
print(exec_result.metadata)
