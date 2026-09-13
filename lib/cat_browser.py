"""File picker and in-terminal viewer for tbx cat."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

import jy


def files(root):
    result = []
    for directory, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in ('.git', 'node_modules', '__pycache__', '.venv'))
        for name in sorted(names):
            path = Path(directory) / name
            if path.is_file():
                result.append(path)
    return result


def detect(path, text):
    suffix = path.suffix.lower()
    if suffix == '.json':
        return 'json'
    if suffix in ('.yaml', '.yml'):
        return 'yaml'
    try:
        json.loads(text)
        return 'json'
    except ValueError:
        pass
    # Avoid classifying every plain text file as a YAML string.
    if shutil.which('yq'):
        try:
            value = json.loads(jy.run(['yq', '-o=json', '.', '-'], text))
            if isinstance(value, (dict, list)):
                return 'yaml'
        except (ValueError, subprocess.CalledProcessError):
            pass
    return 'text'


def environment():
    env = os.environ.copy()
    env['FZF_DEFAULT_OPTS'] = ''
    env.pop('FZF_DEFAULT_OPTS_FILE', None)
    return env


def pick(root, height):
    candidates = files(root)
    if not candidates:
        raise ValueError('No files found in ' + str(root))
    rows = ''.join(f'{i}\t{json.dumps(str(path.relative_to(root)), ensure_ascii=True)}\n' for i, path in enumerate(candidates))
    result = subprocess.run(['fzf', '--height=' + height, '--layout=reverse', '--border',
                             '--delimiter=\t', '--with-nth=2..', '--prompt=cat file > ',
                             '--header=Enter open · Esc quit'], input=rows, text=True,
                            stdout=subprocess.PIPE, env=environment())
    if result.returncode in (1, 130):
        return None
    if result.returncode:
        raise ValueError('File picker failed')
    return candidates[int(result.stdout.split('\t', 1)[0])]


def text_view(path, height, notice='text'):
    env = environment()
    env['TBX_CAT_FILE'] = str(path.resolve())
    command = shlex.join([sys.executable, str(Path(__file__).resolve()), '--preview-text'])
    result = subprocess.run(['fzf', '--disabled', '--height=' + height, '--layout=reverse',
                            '--border', '--prompt=cat > ', '--header=' + notice + ' · ↑↓ scroll · Esc back',
                            '--preview=' + command, '--preview-window=down,80%,wrap',
                            '--bind=up:preview-up,down:preview-down,pgup:preview-page-up,pgdn:preview-page-down'],
                            input=json.dumps(path.name) + '\n', text=True, stdout=subprocess.PIPE, env=env)
    if result.returncode not in (0, 1, 130):
        raise ValueError('Text viewer failed')


def open_file(path, height):
    try:
        text = path.read_text()
    except UnicodeDecodeError:
        text_view(path, height, 'Binary/non-UTF-8 file; displaying replacement characters')
        return
    mode = detect(path, text)
    if mode == 'text':
        text_view(path, height)
        return
    required = ['jq'] + (['yq'] if mode == 'yaml' else [])
    missing = [name for name in required if not shutil.which(name)]
    if missing:
        text_view(path, height, 'Search unavailable; missing ' + ', '.join(missing))
        return
    try:
        document, mode = jy.decode(text, mode)
    except (ValueError, subprocess.CalledProcessError):
        text_view(path, height, 'Invalid or multi-document ' + mode.upper() + '; showing original text')
        return
    jy.browse(document, mode, height, title=path.name)


def main():
    if sys.argv[1:] == ['--preview-text']:
        text = Path(os.environ['TBX_CAT_FILE']).read_text(errors='replace')
        # File contents are text, not terminal escape commands.
        sys.stdout.write(''.join(c if c in '\n\t' or ord(c) >= 32 and ord(c) != 127 else '�' for c in text))
        return
    parser = argparse.ArgumentParser(description='Select a file; JSON/YAML enables key search automatically.')
    parser.add_argument('path', nargs='?', default='.', help='directory to select from, or file to open')
    parser.add_argument('--height', default='80%')
    args = parser.parse_args()
    if not re.fullmatch(r'[1-9][0-9]*%?', args.height):
        parser.error('height must be a positive number or percentage')
    if not shutil.which('fzf'):
        parser.error('fzf required')
    root = Path(args.path).resolve()
    if root.is_file():
        open_file(root, args.height)
        return
    if not root.is_dir():
        parser.error('path does not exist')
    while True:
        selected = pick(root, args.height)
        if selected is None:
            return
        open_file(selected, args.height)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('tbx cat: ' + str(error), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
