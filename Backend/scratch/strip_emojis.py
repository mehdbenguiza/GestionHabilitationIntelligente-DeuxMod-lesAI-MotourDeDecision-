
import os
import re

def strip_emojis(text):
    # This regex removes most emojis and non-ASCII symbols
    return re.sub(r'[^\x00-\x7f]+', '', text)

root_dir = "app/services"
for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Specifically targeting the emojis we know are there
            # but also cleaning non-ASCII in general for safety in print/logs
            new_content = content
            # Replacing common ones with text equivalents if possible, or just stripping
            new_content = new_content.replace("✅", "[OK]")
            new_content = new_content.replace("❌", "[X]")
            new_content = new_content.replace("⚠️", "[!]")
            new_content = new_content.replace("🚀", "[FAST]")
            new_content = new_content.replace("📌", "[NOTE]")
            new_content = new_content.replace("🚨", "[ALERT]")
            new_content = new_content.replace("🔴", "[HIGH]")
            new_content = new_content.replace("🔶", "[MED]")
            new_content = new_content.replace("🌙", "[NIGHT]")
            new_content = new_content.replace("📅", "[DATE]")
            new_content = new_content.replace("📊", "[STATS]")
            new_content = new_content.replace("🤖", "[AI]")
            new_content = new_content.replace("📈", "[UP]")
            new_content = new_content.replace("🧠", "[NN]")
            
            # Final sweep for any other non-ASCII characters in print/log lines
            # (We only want to affect strings, but for now let's just do a general sweep of the whole file 
            # if it's just for this PFE project and encoding issues are blocking us).
            # Actually, let's be more careful: only replace in lines that look like logs or prints or explanations
            lines = []
            for line in new_content.splitlines():
                if any(x in line for x in ["print(", "logger.", "explanation", "label", "message"]):
                    lines.append(strip_emojis(line))
                else:
                    lines.append(line)
            
            new_content = "\n".join(lines)
            
            if new_content != content:
                print(f"Updating {path}")
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
