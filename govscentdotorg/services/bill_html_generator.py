
def is_bullet(text: str) -> bool:
    return (text.startswith('(') and text[2] == ')') or text.startswith('``')


def us_bill_text_to_html(text: str) -> str:
    lines = text.splitlines()
    html = ""
    empty_line_count = 0
    line_count = len(lines)
    index = 0
    while index < line_count:
        line = lines[index]
        line_stripped = line.strip()
        if line_stripped.startswith("______________________________"):
            html += "<div class='separator'></div>"
        elif line_stripped.startswith('[') and line_stripped.endswith(']'):
            html += f"<h3 class='text-center'>{line_stripped.replace('[', '').replace(']', '')}</h3>"
        elif len(line_stripped) < 80 and line_stripped.endswith('CONGRESS'):
            html += f"<h5 class='text-center'>{line_stripped}</h5>"
        elif len(line_stripped) < 80 and line_stripped.endswith('Session'):
            html += f"<h5 class='text-center'>{line_stripped}</h5>"
        elif len(line_stripped) < 50 and line_stripped.find(',') > -1 and len(line_stripped.split(' ')) == 3:
            html += f"<h5 class='date'>{line_stripped}</h5>"
        elif line_stripped.isupper():
            if line_stripped.startswith('SEC'):
                html += f"<h3 class='text-center'>{line_stripped}</h3>"
            else:
                html += f"<h2 class='text-center'>{line_stripped}</h2>"
        elif line_stripped == "<DOC>":
            index += 1
            continue
        elif is_bullet(line_stripped):
            # If the next line after this is not a bullet, and the line after is, for now we assume that the next line is a continuation of this one.
            next_line_index = index + 1
            if next_line_index < line_count - 1:
                is_next_a_bullet = is_bullet(lines[next_line_index])
                if not is_next_a_bullet:
                    next_next_line_index = index + 2
                    if next_next_line_index < line_count - 1:
                        is_next_next_a_bullet = is_bullet(lines[next_next_line_index])
                        if is_next_next_a_bullet:
                            line_stripped += lines[next_line_index]  # lookahead
                            index += 1  # skip next line
            if line_stripped.startswith('``'):
                line_start_quotes_fixed = line_stripped.replace('``', '"')
                html += f"<div class='bullet quoted'>{line_start_quotes_fixed}</div>"
            else:
                if line_stripped[1].isnumeric():
                    html += f"<div class='bullet num'>{line_stripped}</div>"
                else:
                    html += f"<div class='bullet alpha'>{line_stripped}</div>"
        else:
            html += line.replace('``', '"')
            # We compress the text a little by removing some consecutive newline.s
            if empty_line_count < 3 and len(line) < 50:
                html += "<br>"
            if len(line_stripped) == 0:
                empty_line_count += 1
            else:
                empty_line_count = 0
        index += 1
    return html
