from utils import *
import asyncio


file = open("./file.md","r")
file.buffer

# Add file example
url = asyncio.run(upload_file(file.buffer,"test.md","carros"))
public_url = generate_sas_url("test.md","carros")
print(public_url)

# Update file example
url = asyncio.run(update_file(file.buffer,"carros","test4"))
public_url = generate_sas_url("test4","carros")
print(public_url)

# Remove file example
asyncio.run(delete_file("test2.md","carros"))





