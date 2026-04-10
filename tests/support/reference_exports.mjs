import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(typeof chunk === 'string' ? chunk : chunk.toString('utf8'));
  }
  return chunks.join('');
}

function decodeTransformPlugin(mod, spec) {
  if (!spec || typeof spec !== 'object' || Array.isArray(spec)) {
    throw new Error('Unsupported transform plugin payload');
  }

  switch (spec.kind) {
    case 'command_collector':
      return new mod.CommandCollectorPlugin();
    case 'tee': {
      const options = {
        outputDir: spec.outputDir,
      };
      if (typeof spec.targetCommandPatternSource === 'string') {
        options.targetCommandPattern = new RegExp(
          spec.targetCommandPatternSource,
          typeof spec.targetCommandPatternFlags === 'string'
            ? spec.targetCommandPatternFlags
            : '',
        );
      }
      if (spec.timestampMs !== undefined) {
        options.timestamp = new Date(spec.timestampMs);
      }
      return new mod.TeePlugin(options);
    }
    default:
      throw new Error(`Unsupported transform plugin kind: ${String(spec.kind)}`);
  }
}

try {
  const request = JSON.parse(await readStdin());
  const mod = await import(pathToFileURL(request.jsEntry).href);

  let result;
  switch (request.op) {
    case 'get_command_names':
      switch (request.kind) {
        case 'network':
          result = mod.getNetworkCommandNames();
          break;
        case 'python':
          result = mod.getPythonCommandNames();
          break;
        case 'javascript':
          result = mod.getJavaScriptCommandNames();
          break;
        case 'all':
        default:
          result = mod.getCommandNames();
          break;
      }
      break;
    case 'parse':
      result = mod.parse(request.script, request.options ?? {});
      break;
    case 'serialize':
      result = mod.serialize(request.ast);
      break;
    case 'transform_script': {
      const pipeline = new mod.BashTransformPipeline();
      for (const plugin of request.plugins ?? []) {
        pipeline.use(decodeTransformPlugin(mod, plugin));
      }
      result = pipeline.transform(request.script);
      break;
    }
    default:
      throw new Error(`Unknown reference export op: ${String(request.op)}`);
  }

  process.stdout.write(JSON.stringify({ ok: true, result }));
} catch (error) {
  process.stdout.write(
    JSON.stringify({
      ok: false,
      error: {
        type: error?.name ?? 'Error',
        message: error?.message ?? String(error),
      },
    }),
  );
  process.exitCode = 1;
}
