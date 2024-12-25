import argparse
import re
import sys
import yaml

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file_path", type=str, help="Path to the input YAML file")
    parser.add_argument("output_file_path", type=str, help="Path to the output file for the educational configuration language")
    return parser.parse_args()

def read_input_file(input_file_path):
    with open(input_file_path, "r", encoding="utf-8") as file:
        return file.read()

def remove_comments(input_data):
    return re.sub(r'%\{.*?%\}', '', input_data, flags=re.DOTALL)

def preprocess_expressions(input_data):
    def replace_expression(match):
        return f'"{match.group(0)}"'

    return re.sub(r'!\((\+|-)\s+[a-zA-Z][_a-zA-Z0-9]*\s+\d+\)', replace_expression, input_data)

def parse_yaml(input_data):
    try:
        return yaml.safe_load(input_data)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML format: {e}")

def evaluate_expression(expression, constants):
    match = re.match(r'!\((\+|-)\s+([a-zA-Z][_a-zA-Z0-9]*)\s+(\d+)\)', expression)
    if not match:
        raise ValueError(f"Invalid expression format: {expression}")

    operator, name, number = match.groups()
    number = int(number)
    value = constants.get(name)

    if value is None:
        raise ValueError(f"Undefined constant: {name}")

    if operator == "+":
        return value + number
    elif operator == "-":
        return value - number
    else:
        raise ValueError(f"Unsupported operator: {operator}")

def format_output(data):
    result = []

    constants = data.get("constants", {})
    for name, value in constants.items():
        result.append(f"{name}: {value};")

    items = data.get("items", [])
    for item in items:
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, str) and value.startswith("!("):
                    evaluated_value = evaluate_expression(value, constants)
                    result.append(f"{key} = {evaluated_value};")
                elif isinstance(value, list):
                    formatted_array = ", ".join(map(str, value))
                    result.append(f"{key} = ({{ {formatted_array} }});")
                elif isinstance(value, dict):
                    formatted_dict = ", ".join(f"{k} : {v}" for k, v in value.items())
                    result.append(f"{key} = $[ {formatted_dict} ];")
                else:
                    result.append(f"{key} = \"{value}\";")
        elif isinstance(item, str):
            result.append(item)

    return "\n".join(result)

def main():
    args = parse_args()
    try:
        input_data = read_input_file(args.input_file_path)
        input_data = remove_comments(input_data)
        input_data = preprocess_expressions(input_data)

        parsed_data = parse_yaml(input_data)
        output_text = format_output(parsed_data)

        with open(args.output_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(output_text)

        print(f"Output written to {args.output_file_path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

if __name__ == '__main__':
    main()
