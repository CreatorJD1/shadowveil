import sys
from gradio_client import Client, handle_file
c = Client("mcp-tools/FLUX.1-Kontext-Dev", verbose=False)
for f in sys.argv[1:]:
    r = c.upload_files([f]) if hasattr(c,'upload_files') else None
    print(f, r)
