import os
import re
import argparse
from pathlib import Path
from openai import OpenAI


def generate_initial_seed(client, dbms, version, model, sample_text=None):
    """
    Generate initial seeds using LLM
    
    Args:
        client: OpenAI client
        dbms: Target DBMS name
        version: Target DBMS version
        model: LLM model name (e.g., gemini-2.0-flash)
        sample_text: Reference sample text (optional, for zero-shot if None)
        
    Returns:
        Generated SQL statements
    """
    # Template with samples (few-shot)
    prompt_template_with_sample = """You need to generate high-quality initial seeds for DBMS fuzz testing．An initial seed consists of multiple SQL statements and only contain SQL statements
Follow the steps below to reason step by step and generate the initial seeds:
Step 1: Grammatical and Semantic Correctness 
Ensure that all SQL statements in the initial seeds conform to the syntax rules and semantic logic of the target database. 
Step 2: SQL Quality Assurance 
The initial seeds should contain sufficient number of SQL statements, with rich usage of various SQL keywords.
Step 3: Target-Specific SQL Features 
Incorporate SQL statements that use database-specific keywords or features based on the target DBMS to make the initial seeds tailored and effective. 
Step 4: Use Sample as Reference 
Refer to the provided sample initial seed in the sample section to understand the required format.
Step 5: Completeness Check 
After generation, perform a thorough validation of the seed: 
- If any SQL syntax is incorrect for the target DBMS, it must be fixed. 
- If there are semantic issues (e.g., a statement uses a table that hasn't been created), insert necessary preorder statements in the seed in a logically consistent order. 
Generate one high-quality and well-structured initial seed for the {dbms} version in {version}. 
Wrap generated initial seeds using the following format: 
'\\n```sql\\n (generated initial seeds) \\n```\\n'
A sample of initial seeds:
{sample}
"""
    
    # Template without samples (zero-shot)
    prompt_template_zero_shot = """You need to generate high-quality initial seeds for DBMS fuzz testing．An initial seed consists of multiple SQL statements and only contain SQL statements
Follow the steps below to reason step by step and generate the initial seeds:
Step 1: Grammatical and Semantic Correctness 
Ensure that all SQL statements in the initial seeds conform to the syntax rules and semantic logic of the target database. 
Step 2: SQL Quality Assurance 
The initial seeds should contain sufficient number of SQL statements, with rich usage of various SQL keywords.
Step 3: Target-Specific SQL Features 
Incorporate SQL statements that use database-specific keywords or features based on the target DBMS to make the initial seeds tailored and effective. 
Step 4: Completeness Check 
After generation, perform a thorough validation of the seed: 
- If any SQL syntax is incorrect for the target DBMS, it must be fixed. 
- If there are semantic issues (e.g., a statement uses a table that hasn't been created), insert necessary preorder statements in the seed in a logically consistent order. 
Generate one high-quality and well-structured initial seed for the {dbms} version in {version}. 
Wrap generated initial seeds using the following format: 
'\\n```sql\\n (generated initial seeds) \\n```\\n'
"""
    
    # Select template based on whether sample is provided
    if sample_text:
        prompt_template = prompt_template_with_sample.format(
            dbms=dbms,
            version=version,
            sample=sample_text
        )
    else:
        prompt_template = prompt_template_zero_shot.format(
            dbms=dbms,
            version=version
        )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt_template}],
    )

    generated = response.choices[0].message.content

    match = re.search(r"```sql\s*(.*?)\s*```", generated, re.DOTALL)
    if match:
        extracted_sql = match.group(1).strip()
    else:
        raise Exception(f"Failed to extract SQL from {generated}")

    return extracted_sql


def main(input_folder, output_folder, target_dbms, target_version, api_key, base_url, model, count):
    """
    Main function: generate initial seeds for DBMS fuzzing
    
    Args:
        input_folder: Path to input folder (containing reference samples), optional for zero-shot
        output_folder: Path to output folder
        target_dbms: Target DBMS name
        target_version: Target version
        api_key: API key
        base_url: API base URL
        model: LLM model name
        count: Number of seeds to generate
    """
    # Create output folder
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # Initialize OpenAI client
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    # Get list of input files (if input folder is provided)
    input_files = []
    if input_folder:
        input_files = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
        
        if not input_files:
            print(f"Warning: No files found in input folder {input_folder}")
            print("Will use zero-shot generation instead")
            input_folder = None

    # Generate specified number of seeds
    generated_count = 0
    file_index = 0
    counter = 1
    
    while generated_count < count:
        sample_content = None
        filename = "zero-shot"
        
        # If input folder is provided, use samples
        if input_folder:
            filename = input_files[file_index % len(input_files)]
            input_path = os.path.join(input_folder, filename)

            try:
                # Read file content as sample
                with open(input_path, 'r', encoding='utf-8') as f:
                    sample_content = f.read()
            except Exception as e:
                print(f"✗ Failed to read sample {filename}: {str(e)}")
                file_index += 1
                continue

        try:
            # Generate initial seed
            print(f"[{generated_count + 1}/{count}] Generating seed (based on {filename})...")
            generated_content = generate_initial_seed(client, target_dbms, target_version, model, sample_content)

            # Generate output filename
            output_filename = f"GSeed_{counter}.txt"
            output_path = os.path.join(output_folder, output_filename)

            # Save generated result
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(generated_content)

            print(f"✓ Saved to {output_filename}")
            generated_count += 1
            counter += 1

        except Exception as e:
            print(f"✗ Failed to generate seed: {str(e)}")
        
        file_index += 1

    print(f"\nCompleted! Generated {generated_count} initial seeds and saved to {output_folder}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate initial seeds for DBMS fuzzing using LLM"
    )
    
    parser.add_argument(
        "-i", "--input",
        type=str,
        required=False,
        default=None,
        help="Path to input folder (containing reference sample SQL files). If not provided, zero-shot generation will be used"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        required=True,
        help="Path to output folder"
    )
    
    parser.add_argument(
        "-d", "--dbms",
        type=str,
        required=True,
        help="Target DBMS name (e.g., PostgreSQL, MySQL, SQLite, ...)"
    )
    
    parser.add_argument(
        "-v", "--version",
        type=str,
        required=True,
        help="Target DBMS version"
    )
    
    parser.add_argument(
        "-k", "--api-key",
        type=str,
        required=True,
        help="API key"
    )
    
    parser.add_argument(
        "-u", "--base-url",
        type=str,
        required=True,
        help="API base URL"
    )
    
    parser.add_argument(
        "-m", "--model",
        type=str,
        required=True,
        help="LLM model name (e.g., gemini-2.0-flash, gpt-4, claude-3-opus)"
    )
    
    parser.add_argument(
        "-c", "--count",
        type=int,
        default=10,
        help="Number of seeds to generate (default: 10)"
    )
    
    args = parser.parse_args()
    
    main(
        input_folder=args.input,
        output_folder=args.output,
        target_dbms=args.dbms,
        target_version=args.version,
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model,
        count=args.count
    )
