#!/usr/bin/env python3
"""Interactive, one-level JSON/YAML navigation using jq, yq and fzf."""
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile


def run(args, text=None):
    return subprocess.run(args, input=text, text=True, capture_output=True, check=True).stdout


def decode(text, mode):
    if not text.strip():
        raise ValueError('Input is empty')
    if mode == 'auto':
        try:
            json.loads(text)
            mode = 'json'
        except ValueError:
            mode = 'yaml'
    if mode == 'yaml':
        text = run(['yq', '-o=json', '.', '-'], text)
    # jq is the data engine; reject ambiguous multi-document streams.
    value = json.loads(run(['jq', '-s', 'if length == 1 then .[0] else error("Expected one document") end'], text))
    return value, mode


def keys(value):
    if isinstance(value, dict):
        return list(value)
    if isinstance(value, list):
        return list(range(len(value)))
    return []


def matching(value, query):
    return [key for key in keys(value) if query.casefold() in str(key).casefold()]


def scoped(document, path):
    return json.loads(run(['jq', '--argjson', 'path', json.dumps(path), 'getpath($path)'], json.dumps(document)))


def render(value, mode):
    text = json.dumps(value, ensure_ascii=False)
    if mode == 'yaml':
        return run(['yq', '-P', '-p=json', '-o=yaml', '.', '-'], text)
    return run(['jq', '.', '-'], text)


def preview(value, query, mode):
    matched = matching(value, query)
    if isinstance(value, dict):
        filtered = {key: value[key] for key in matched}
    elif isinstance(value, list):
        # Preserve original indices when filtering array entries.
        filtered = {str(key): value[key] for key in matched} if query else value
    else:
        filtered = value
    text = render(filtered, mode)
    if query:
        lines = text.splitlines()
        for index, line in enumerate(lines):
            is_key = (mode == 'json' and line.startswith('  "') and not line.startswith('   ')) or (mode == 'yaml' and line and not line[0].isspace() and ':' in line)
            if is_key:
                # Only color the key portion, never nested keys or values.
                boundary = re.match(r'  "(?:[^"\\]|\\.)*"\s*:', line) if mode == 'json' else None
                end = boundary.end() - 1 if boundary else line.find(':')
                prefix = re.sub(re.escape(query), lambda m: '\x1b[31m' + m[0] + '\x1b[0m', line[:end], flags=re.I)
                lines[index] = prefix + line[end:]
        text = '\n'.join(lines) + '\n'
    return text


def helper(action, query):
    state = json.loads(Path(os.environ['TBX_JY_STATE']).read_text())
    value = state['value']
    if action == 'preview':
        sys.stdout.write(preview(value, query, state['mode']))
    else:
        all_keys = keys(value)
        for index, key in enumerate(all_keys):
            if query.casefold() not in str(key).casefold():
                continue
            # Opaque row IDs keep shell metacharacters and newlines out of paths.
            label = json.dumps(key, ensure_ascii=True)
            print(f'{index}\t{label}')
        if not all_keys and not query:
            print('-1\t[value]')


def browse(document, mode, height, title="cat"):
    path = []
    with tempfile.TemporaryDirectory(prefix='tbx-jy-') as directory:
        state = Path(directory) / 'state.json'
        env = os.environ.copy()
        env['TBX_JY_STATE'] = str(state)
        env['FZF_DEFAULT_OPTS'] = ''
        env.pop('FZF_DEFAULT_OPTS_FILE', None)
        env.pop('NO_COLOR', None)
        command = shlex.join([sys.executable, str(Path(__file__).resolve())])
        while True:
            value = scoped(document, path)
            state.write_text(json.dumps(dict(value=value, mode=mode)))
            prompt = '.' + ''.join('[' + json.dumps(key, ensure_ascii=True) + ']' for key in path)
            args = ['fzf', '--ansi', '--color=16', '--disabled', '--delimiter=\t', '--with-nth=2..',
                    '--height=' + height, '--layout=reverse', '--border', '--no-sort',
                    '--border-label=' + json.dumps(title, ensure_ascii=True),
                    '--prompt=' + ('jq ' if mode == 'json' else 'yq ') + prompt + ' > ', '--header=↑↓ select/scroll · Enter drill · Alt-← back · Ctrl-O output scope · Esc files',
                    '--preview-window=down,65%,border-top', '--preview=' + command + ' --internal preview {q}',
                    '--bind=start:reload(' + command + " --internal list '')",
                    '--bind=change:reload(' + command + ' --internal list {q})+refresh-preview',
                    '--bind=up:up+preview-up,down:down+preview-down,alt-up:preview-up,alt-down:preview-down',
                    '--bind=pgup:preview-page-up,pgdn:preview-page-down',
                    '--expect=enter,alt-left,ctrl-b,ctrl-o']
            result = subprocess.run(args, input='', text=True, stdout=subprocess.PIPE, env=env)
            if result.returncode in (1, 130):
                return
            if result.returncode:
                raise ValueError('fzf failed')
            lines = result.stdout.splitlines()
            if not lines:
                return
            action = lines[0]
            if action in ('alt-left', 'ctrl-b'):
                path = path[:-1]
                continue
            if action == 'ctrl-o':
                sys.stdout.write(render(value, mode))
                return
            if len(lines) < 2:
                continue
            index = int(lines[1].split('\t')[0])
            if index == -1:
                continue
            key = keys(value)[index]
            path.append(key)


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--internal':
        helper(sys.argv[2], sys.argv[3])
        return
    raise ValueError('Open the file browser with tbx cat')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        detail = error.stderr if isinstance(error, subprocess.CalledProcessError) else str(error)
        print('tbx jy: ' + detail.strip(), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
