import os
import csv
import anthropic
from dotenv import load_dotenv
from pathlib import Path
import csv
from io import StringIO


load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API'))

def read_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_structured_commands(text):
    prompt = f"""Analyze the text and extract ALL Linux commands mentioned, even if they are part of explanations.
For each command, provide multiple practical examples in CSV format with three columns:
1. command: The command name
2. prompt: Clear description of what the user wants to do
3. output: Exact command with flags to accomplish the task

Example output format:
command,prompt,output
ls,list files in current directory,ls
ls,show all hidden files,ls -a
ls,show detailed file information,ls -l
ls,show files sorted by time,ls -t
ls,show all files with human-readable sizes,ls -lah

Rules:
1. Extract EVERY command mentioned in the text
2. Include any specific flags or options discussed
3. Add practical examples beyond what's in the text
4. Provide at least 5 examples per command
5. Make each prompt clear and specific
6. Ensure outputs are exact working commands

Text to analyze:
{text}

Remember: Extract ALL commands and provide diverse, practical examples. ONLY OUTPUT CSV! NO OTHER TEXT JUST THE CSV!"""
    
    message = client.messages.create(
        model="claude-3-5-haiku-latest",
        max_tokens=8192,
        temperature=0.5,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    try:
        # Split the response into lines and parse CSV
        csv_data = []
        csv_reader = csv.DictReader(StringIO(message.content[0].text))
        for row in csv_reader:
            csv_data.append(row)
        return [{"command": row["command"], 
                "examples": [{"prompt": row["prompt"], "output": row["output"]}]} 
               for row in csv_data]
    except:
        return []

def main():
    script_dir = Path(__file__).parent
    commands_dir = script_dir / 'commands'
    output_file = script_dir / 'linux_commands.csv'    
    file_exists = Path(output_file).exists() and Path(output_file).stat().st_size > 0
    

    with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['command', 'prompt', 'output']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        

        if not file_exists:
            writer.writeheader()
            csvfile.flush()
        
        # Process each text file
        for text_file in sorted(commands_dir.glob('*.txt')):
            print(f"Processing {text_file.name}...")
            text_content = read_text_file(text_file)
            structured_commands = get_structured_commands(text_content)
            print(f"Found {len(structured_commands)} commands in {text_file.name}")
            # Write commands and their examples to CSV
            for command_data in structured_commands:
                command_name = command_data['command']
                for example in command_data['examples']:
                    writer.writerow({
                        'command': command_name,
                        'prompt': example['prompt'],
                        'output': example['output']
                    })
                csvfile.flush()
            
            print(f"Processed {text_file.name}")

if __name__ == "__main__":
    main()
