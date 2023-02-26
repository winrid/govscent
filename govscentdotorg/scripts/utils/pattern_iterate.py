from os import scandir, path


# example pattern: [congress]/bills/[bill_type]/[bill_type_and_number]/text-versions/[status_code]/[package]
# not super optimized, goal is simplicity.
def iterate_dir_for_pattern(input_dir_path: str, pattern: str, depth: int, attributes: dict):
    pattern_tokens = pattern.split("/")
    pattern_tokens_len = len(pattern_tokens)
    if depth == pattern_tokens_len:
        yield attributes
        return
    next_dir_pattern = pattern_tokens[depth]
    for entry in scandir(input_dir_path):
        print(depth, entry.name, next_dir_pattern)
        if entry.name.startswith('.'):
            continue
        entry_dir_path = path.join(input_dir_path, entry.name)
        if next_dir_pattern.startswith('['):
            attribute_name = next_dir_pattern.replace('[', '').replace(']', '')
            if depth + 1 == pattern_tokens_len:
                attributes[attribute_name] = path.join(input_dir_path, entry.name)
            else:
                attributes[attribute_name] = entry.name
            yield from iterate_dir_for_pattern(entry_dir_path, pattern, depth + 1, attributes)
        elif next_dir_pattern == entry.name:
            yield from iterate_dir_for_pattern(entry_dir_path, pattern, depth + 1, attributes)
