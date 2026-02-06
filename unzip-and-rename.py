import os
import re
import subprocess
import shutil
from datetime import datetime

SEVEN_ZIP = r"C:\WINDOWS\system32\7z"
CURRENT_DIR = os.getcwd()
LOG_FILE = os.path.join(CURRENT_DIR, "extraction_log.txt")
EXTRACTED_FILE = os.path.join(CURRENT_DIR, ".extracted_rars")

# Files to remove after extraction
FILES_TO_REMOVE = ["freeeducationweb - link to website.url", "Read me First.txt"]

def log_message(message: str):
  """Log message to both console and file"""
  timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  log_entry = f"[{timestamp}] {message}"
  print(log_entry)
  try:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
      f.write(log_entry + "\n")
  except Exception as e:
    print(f"Warning: Could not write to log file: {e}")

def load_extracted_rars():
  """Load list of already extracted .rar files"""
  if os.path.exists(EXTRACTED_FILE):
    try:
      with open(EXTRACTED_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)
    except:
      return set()
  return set()

def save_extracted_rar(filename: str):
  """Save extracted .rar filename to tracking file"""
  try:
    with open(EXTRACTED_FILE, "a", encoding="utf-8") as f:
      f.write(filename + "\n")
  except Exception as e:
    log_message(f"Warning: Could not save to tracking file: {e}")

def clean_name(name: str) -> str:
  # Remove [anything] prefix and .rar
  name = os.path.splitext(name)[0]
  name = re.sub(r"^\[.*?\]\s*", "", name)
  return name.strip()

def remove_unwanted_files(directory):
  """Remove unwanted files from directory"""
  try:
    for item in os.listdir(directory):
      item_path = os.path.join(directory, item)
      # Check if file matches any of the files to remove (case-insensitive)
      if item.lower() in [f.lower() for f in FILES_TO_REMOVE]:
        try:
          if os.path.isfile(item_path):
            os.remove(item_path)
            log_message(f"  Removed file: {item}")
        except Exception as e:
          log_message(f"  Warning: Could not remove {item}: {e}")
  except Exception as e:
    log_message(f"  Warning: Error checking for unwanted files: {e}")

def move_nested_content(output_dir):
  """Move all nested content up to the output directory, removing intermediate folders"""
  try:
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
      iteration += 1
      items = os.listdir(output_dir)
      items = [item for item in items if not item.startswith('.')]

      if len(items) != 1:
        break

      nested_path = os.path.join(output_dir, items[0])
      if not os.path.isdir(nested_path):
        break

      # Move all contents from nested folder to parent
      try:
        for item in os.listdir(nested_path):
          src = os.path.join(nested_path, item)
          dst = os.path.join(output_dir, item)

          # If destination exists, remove it first
          if os.path.exists(dst):
            try:
              if os.path.isdir(dst):
                shutil.rmtree(dst)
              else:
                os.remove(dst)
            except Exception as e:
              log_message(f"  Warning: Could not remove existing {item}: {e}")

          # Move the item
          shutil.move(src, dst)

        # Remove empty nested folder
        try:
          os.rmdir(nested_path)
          log_message(f"  Removed intermediate folder: {items[0]}")
        except Exception as e:
          log_message(f"  Warning: Could not remove folder {items[0]}: {e}")
      except Exception as e:
        log_message(f"  Warning: Error moving contents: {e}")
        break
  except Exception as e:
    log_message(f"  Warning: Error in move_nested_content: {e}")

try:
  extracted_rars = load_extracted_rars()
  count = 0

  for file in os.listdir(CURRENT_DIR):
    if file.lower().endswith(".rar"):
      if file in extracted_rars:
        log_message(f"⊘ Skipping already extracted: {file}")
        continue

      count += 1
      try:
        rar_path = os.path.join(CURRENT_DIR, file)
        folder_name = clean_name(file)
        output_dir = os.path.join(CURRENT_DIR, folder_name)

        os.makedirs(output_dir, exist_ok=True)

        log_message(f"Extracting ({count}): {file} -> {folder_name}/")

        subprocess.run([
            SEVEN_ZIP,
            "x",
            rar_path,
            f"-o{output_dir}",
            "-y"
        ], check=True)

        # Move nested content if needed
        move_nested_content(output_dir)

        # Remove unwanted files
        remove_unwanted_files(output_dir)

        log_message(f"✓ Successfully extracted: {folder_name}")

        # Mark as extracted
        save_extracted_rar(file)

      except subprocess.CalledProcessError as e:
        log_message(f"✗ ERROR extracting {file}: Command failed")
      except Exception as e:
        log_message(f"✗ ERROR processing {file}: {type(e).__name__}")

  log_message(f"Processing complete. Extracted {count} new archives.")

except Exception as e:
  log_message(f"✗ FATAL ERROR: {type(e).__name__}")
