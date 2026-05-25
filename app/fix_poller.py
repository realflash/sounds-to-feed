with open("src/backend/core/poller.py", "r") as f:
    content = f.read()

# Replace the inner imports
content = content.replace("        import urllib.parse\n        import httpx\n        from datetime import datetime\n        \n", "")
# Add to top of file
new_imports = "import httpx\nimport urllib.parse\nfrom datetime import datetime\n"

content = content.replace("import os\n", "import os\n" + new_imports)

with open("src/backend/core/poller.py", "w") as f:
    f.write(content)
print("Fixed poller imports")
