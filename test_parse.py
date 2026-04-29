import re
text = "**HUMAN**: Hello!\n\n**AI**: Hi there! How can I help?\n\n**HUMAN**: What is NVDA?\n\n**AI**: NVDA is Nvidia."
chunks = re.split(r'\*\*(HUMAN|AI)\*\*:', text)
print("CHUNKS:", chunks)
for i in range(1, len(chunks), 2):
    print("ROLE:", chunks[i], "CONTENT:", chunks[i+1].strip())
