import pytest
import tempfile
import os
from main.py import (
    read_input_file,
    remove_comments,
    preprocess_expressions,
    parse_yaml,
    evaluate_expression,
    format_output,
    main
)


def create_temp_file(content):
    temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml")
    temp_file.write(content)
    temp_file.close()
    return temp_file.name

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
      return file.read()


def test_read_input_file():
    temp_file_name = create_temp_file("test content")
    assert read_input_file(temp_file_name) == "test content"
    os.unlink(temp_file_name)

def test_remove_comments():
    assert remove_comments("abc %{comment%} def") == "abc  def"
    assert remove_comments("abc %{multi\nline\ncomment%} def") == "abc  def"
    assert remove_comments("abc %{comment") == "abc %{comment" #Not a complete comment
    assert remove_comments("abc %{ comment %} def %{another %} ghi") == "abc  def  ghi"
    assert remove_comments("No comments") == "No comments"

def test_preprocess_expressions():
    assert preprocess_expressions("!(+ a 10)") == '"!(+ a 10)"'
    assert preprocess_expressions("!(- b 20)") == '"!(- b 20)"'
    assert preprocess_expressions("!(- c 30) and !(+ d 40)") == '"!(- c 30)" and "!(+ d 40)"'
    assert preprocess_expressions("!(* a 10)") == "!(+ a 10)" #Invalid expression should not be processed
    assert preprocess_expressions("!(- a)") == "!(- a)" #Invalid expression should not be processed
    assert preprocess_expressions("abc") == "abc"

def test_parse_yaml_valid():
    valid_yaml = """
    constants:
      a: 10
    items:
      - x: 20
      - y: "hello"
    """
    parsed_data = parse_yaml(valid_yaml)
    assert parsed_data == {
        "constants": {"a": 10},
        "items": [{"x": 20}, {"y": "hello"}]
    }

def test_parse_yaml_invalid():
    invalid_yaml = "invalid yaml"
    with pytest.raises(ValueError, match="Invalid YAML format"):
        parse_yaml(invalid_yaml)

def test_evaluate_expression_valid():
    constants = {"a": 10, "b": 20}
    assert evaluate_expression("!(+ a 5)", constants) == 15
    assert evaluate_expression("!(- b 3)", constants) == 17

def test_evaluate_expression_invalid():
    constants = {"a": 10}
    with pytest.raises(ValueError, match="Invalid expression format"):
        evaluate_expression("!(a + 5)", constants)
    with pytest.raises(ValueError, match="Undefined constant: c"):
      evaluate_expression("!(+ c 5)", constants)
    with pytest.raises(ValueError, match="Unsupported operator: *"):
        evaluate_expression("!(* a 5)", constants)

def test_format_output():
    data = {
        "constants": {"a": 10, "b": 20},
        "items": [
            {"x": "hello"},
            {"y": "!(+ a 5)"},
            {"z": ["1", "2", "3"]},
            {"w": {"p": 1, "q": 2}}
        ]
    }
    expected_output = """a: 10;
b: 20;
x = "hello";
y = 15;
z = ({ 1, 2, 3 });
w = $[ p : 1, q : 2 ];"""
    assert format_output(data).strip() == expected_output.strip()

def test_main_valid_input():
    input_content = """
    constants:
      a: 10
    items:
      - x: "hello"
      - y: "!(+ a 5)"
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as input_file:
        input_file.write(input_content)
        input_file_path = input_file.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ecl") as output_file:
        output_file_path = output_file.name
    try:
      main() #This triggers args parsing so can't use mock arguments, as they are set with argparse
      # So we need to set them via environment variable
      os.environ["INPUT_FILE_PATH"] = input_file_path
      os.environ["OUTPUT_FILE_PATH"] = output_file_path
      sys.argv = ["test_script", input_file_path, output_file_path]
      main()
      output_text = read_file(output_file_path)
      assert "a: 10;" in output_text
      assert "x = \"hello\";" in output_text
      assert "y = 15;" in output_text

    finally:
      os.unlink(input_file_path)
      os.unlink(output_file_path)


def test_main_invalid_input():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as input_file:
        input_file.write("invalid yaml")
        input_file_path = input_file.name
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ecl") as output_file:
        output_file_path = output_file.name
    try:
        os.environ["INPUT_FILE_PATH"] = input_file_path
        os.environ["OUTPUT_FILE_PATH"] = output_file_path
        sys.argv = ["test_script", input_file_path, output_file_path]
        with pytest.raises(ValueError, match="Invalid YAML format"):
            main()
    finally:
      os.unlink(input_file_path)
      os.unlink(output_file_path)
