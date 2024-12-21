import argparse
import glob
import os
import shutil
from pathlib import Path

from bs4 import BeautifulSoup


def create_flat_filename(original_path):
  parts = Path(original_path).parts

  if parts[0] in {'html', '_modules', '_static', '_sources'}:
    parts = parts[1:]

  return '_'.join(parts)


def copy_to_flat_directory(source_dir, target_dir):
  path_mapping = {}

  os.makedirs(target_dir, exist_ok=True)

  for root, _, files in os.walk(source_dir):
    for file in files:
      source_path = os.path.join(root, file)
      relative_path = os.path.relpath(source_path, source_dir)
      new_filename = create_flat_filename(relative_path)
      target_path = os.path.join(target_dir, new_filename)

      if os.path.exists(target_path):
        base, ext = os.path.splitext(new_filename)
        counter = 1
        while os.path.exists(target_path):
          new_filename = f'{base}_{counter}{ext}'
          target_path = os.path.join(target_dir, new_filename)
          counter += 1

      shutil.copy2(source_path, target_path)
      path_mapping[relative_path] = new_filename

  return path_mapping


def update_html_references(file_path, path_mapping):
  with open(file_path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

  for link in soup.find_all(['a', 'link', 'script', 'img']):
    if link.has_attr('href'):
      href = link['href']

      for _, _ in path_mapping.items():
        if href.startswith('_'):
          old_parts = href.split('/')
          if len(old_parts) > 1:
            new_href = create_flat_filename(href)
            link['href'] = new_href
        elif href in path_mapping:
          link['href'] = path_mapping[href]

    if link.has_attr('src'):
      src = link['src']

      for _, _ in path_mapping.items():
        if src.startswith('_'):
          old_parts = src.split('/')
          if len(old_parts) > 1:
            new_src = create_flat_filename(src)
            link['src'] = new_src
        elif src in path_mapping:
          link['src'] = path_mapping[src]

  with open(file_path, 'w', encoding='utf-8') as f:
    f.write(str(soup))


def parse_args():
  parser = argparse.ArgumentParser(
    description='Flatten a Sphinx documentation directory structure and update HTML references.'
  )

  parser.add_argument(
    '-s', '--source', required=True, help='Source directory containing Sphinx documentation'
  )

  parser.add_argument(
    '-o', '--output', required=True, help='Output directory for flattened documentation'
  )

  return parser.parse_args()


def main():
  args = parse_args()

  print(f'Copying files from {args.source} to flat directory {args.output}...')

  path_mapping = copy_to_flat_directory(args.source, args.output)

  print('Updating references in HTML files...')
  html_files = glob.glob(os.path.join(args.output, '*.html'))

  for html_file in html_files:
    print(f'Processing {html_file}...')
    update_html_references(html_file, path_mapping)

  print(f"\nDone! Flattened documentation is in '{args.output}' directory.")


if __name__ == '__main__':
  main()
