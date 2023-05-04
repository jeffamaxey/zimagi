#!/opt/conda/envs/zimagi/bin/python
#-------------------------------------------------------------------------------
import sys
import os
import re
#-------------------------------------------------------------------------------

key_path = sys.argv[1]
if not (
    components := re.search(
        r'^(\-+[^\-]+\-+)\s+(.+)\s+(\-+[^\-]+\-+)$', sys.argv[2], re.DOTALL
    )
):
    raise Exception(f"Key {key_path} entered is not correct format: {sys.argv[2]}")

key_prefix = components[1]
key_material = "\n".join(re.split(r'\s+', components[2]))
key_suffix = components[3]
with open(key_path, 'w') as file:
    file.write(f"{key_prefix}\n{key_material}\n{key_suffix}")
    os.chmod(key_path, 0o660)
