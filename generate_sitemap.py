import os
import urllib.parse
import subprocess
import sys

BASE_URL = "https://kai9987kai.co.uk"

EXCLUDED = {
    ".git",
    ".github",
    "node_modules",
    "__pycache__"
}

def get_files_from_git(repo_path):
    """Get list of tracked files in git repository HEAD."""
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "ls-tree", "-r", "HEAD", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Warning: git command failed for {repo_path}: {e}")
        return None
    except FileNotFoundError:
        print("Warning: git executable not found.")
        return None

def get_files_from_walk(scan_path):
    """Fall back to walking the filesystem if git is not available."""
    found_files = []
    for root, dirs, files in os.walk(scan_path):
        # Exclude directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDED]
        for file in files:
            full_path = os.path.relpath(os.path.join(root, file), scan_path)
            # Normalize to forward slashes
            full_path = full_path.replace("\\", "/")
            found_files.append(full_path)
    return found_files

def main():
    # Detect target directory: default to "repo_shallow" if it exists, otherwise "."
    target_dir = "repo_shallow"
    if not os.path.exists(target_dir):
        target_dir = "."

    print(f"Scanning target directory: {target_dir}")

    # Check if target_dir is a git repository (has .git folder)
    is_git_repo = os.path.exists(os.path.join(target_dir, ".git"))
    
    files = None
    if is_git_repo:
        print("Git repository detected. Querying tracked files via git...")
        files = get_files_from_git(target_dir)

    if files is None:
        print("Falling back to walking filesystem...")
        files = get_files_from_walk(target_dir)

    urls = []
    
    # Process files
    for file_path in files:
        parts = file_path.split("/")
        if any(part in EXCLUDED for part in parts):
            continue

        # Check file extensions
        if file_path.lower().endswith((".html", ".htm", ".php", ".xhtml")):
            # Url-encode path parts
            encoded = "/".join(urllib.parse.quote(part) for part in parts)
            urls.append(f"{BASE_URL}/{encoded}")

            # If it's an index.html file in a subdirectory, add the directory index URL
            if parts[-1].lower() == "index.html" and len(parts) > 1:
                dir_path = "/".join(urllib.parse.quote(part) for part in parts[:-1])
                urls.append(f"{BASE_URL}/{dir_path}/")

    urls = sorted(set(urls))

    with open("Sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')

        for url in urls:
            f.write("  <url>\n")
            f.write(f"    <loc>{url}</loc>\n")
            f.write("    <priority>0.80</priority>\n")
            f.write("  </url>\n")

        f.write("</urlset>\n")

    print(f"Generated Sitemap.xml with {len(urls)} URLs")

if __name__ == "__main__":
    main()
