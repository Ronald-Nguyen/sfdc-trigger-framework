import os
import subprocess
import xml.etree.ElementTree as ET
import re

def create_ruleset_file(filename="pmd-ruleset.xml"):
    """Creates the PMD ruleset XML file."""
    content = """<?xml version="1.0" encoding="UTF-8"?>
<ruleset name="Custom Apex Rules"
         xmlns="http://pmd.sourceforge.net/ruleset/2.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://pmd.sourceforge.net/ruleset/2.0.0 https://pmd.github.io/schema/ruleset_2_0_0.xsd">

    <description>Custom Cognitive Complexity threshold</description>

    <rule ref="category/apex/design.xml/CognitiveComplexity">
        <properties>
            <property name="methodReportLevel" value="1"/>
        </properties>
    </rule>

</ruleset>
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created {filename}")

def run_pmd_command(ruleset="pmd-ruleset.xml", report_file="pmd-report.xml", src_dir="./src"):
    """Executes the PMD check command using PowerShell."""
    # Note: 'pmd' must be in your system PATH for this to work
    command = [
        "pmd", "check",
        "--dir", src_dir,
        "--rulesets", ruleset,
        "--format", "xml",
        "--report-file", report_file
    ]
    
    print(f"Executing PMD analysis on {src_dir}...")
    
    try:
        # shell=True is often required on Windows to find the pmd.bat/ps1 wrapper
        subprocess.run(command, check=True, shell=True)
        print(f"Analysis complete. Report generated at {report_file}")
    except subprocess.CalledProcessError as e:
        # PMD returns non-zero exit codes if violations are found, which is expected here.
        # We only want to crash if the command actually failed to run (like command not found).
        if e.returncode > 0:
            print(f"PMD finished with violations (Exit code {e.returncode}). Proceeding to parsing.")
        else:
            print(f"Error running PMD: {e}")

def parse_and_summarize(report_file="pmd-report.xml", output_file="complexity-summary.txt"):
    """Parses the XML report and generates a text summary."""
    if not os.path.exists(report_file):
        print(f"Error: {report_file} not found.")
        return

    tree = ET.parse(report_file)
    root = tree.getroot()
    
    # Namespace handling for PMD reports
    ns = {'pmd': 'http://pmd.sourceforge.net/report/2.0.0'}
    
    file_complexities = {}

    # Regex to extract the complexity number from the message
    # Pattern looks for "cognitive complexity of X,"
    complexity_pattern = re.compile(r"cognitive complexity of (\d+)")

    for file_elem in root.findall('pmd:file', ns):
        filename = file_elem.get('name')
        total_complexity = 0
        
        for violation in file_elem.findall('pmd:violation', ns):
            rule = violation.get('rule')
            if rule == 'CognitiveComplexity':
                message = violation.text.strip() if violation.text else ""
                match = complexity_pattern.search(message)
                if match:
                    complexity_score = int(match.group(1))
                    total_complexity += complexity_score

        file_complexities[filename] = total_complexity

    # Write the summary text file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Project Structure & Complexity Report\n")
        f.write("=====================================\n\n")
        
        # Sort by filename for cleaner structure
        for filename in sorted(file_complexities.keys()):
            score = file_complexities[filename]
            f.write(f"{filename}: [Total Complexity: {score}]\n")
            
    print(f"Summary generated at {output_file}")

if __name__ == "__main__":
    # 1. Create the XML configuration
    create_ruleset_file()
    
    # 2. Run the PMD command
    # Ensure you have a ./src folder, otherwise create a dummy one for testing
    if not os.path.exists("./src"):
        print("Warning: './src' directory not found. Please ensure it exists before running.")
    else:
        run_pmd_command()
        
    # 3. Parse and create text summary
    # If you want to test with your dummy XML data instead of running PMD,
    # comment out run_pmd_command() and ensure pmd-report.xml exists.
    parse_and_summarize()