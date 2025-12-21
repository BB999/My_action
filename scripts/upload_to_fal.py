#!/usr/bin/env python3
"""
FAL.ai にファイルをアップロードするスクリプト
GitHub Actions用
"""
import os
import sys
import fal_client

def main():
    if len(sys.argv) < 2:
        print("Usage: python upload_to_fal.py <file_path>")
        sys.exit(1)

    image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        sys.exit(1)

    print(f"Uploading {image_path} to FAL...")

    try:
        url = fal_client.upload_file(image_path)
        print(f"Upload successful!")
        print(f"URL: {url}")

        # GitHub Outputに書き込み
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f"url={url}\n")
                f.write("status=success\n")

    except Exception as e:
        print(f"Upload failed: {e}")
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write("url=unknown\n")
                f.write("status=failed\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
