from step_parser import parse_step_file, extract_step_components

data = parse_step_file("test.step")
components = extract_step_components(data)
print(components)