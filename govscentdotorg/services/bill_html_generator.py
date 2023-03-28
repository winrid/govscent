
def is_bullet(text: str) -> bool:
    return (text.startswith('(') and text[2] == ')') or text.startswith('``') or text.startswith('Whereas')


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
        elif line_stripped == "<DOC>" or line_stripped == "&lt;DOC&gt;":
            index += 1
            continue
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
        elif is_bullet(line_stripped):
            # TODO keep track of bullet depth.
            # If the next line after this is not a bullet, and the line after is, for now we assume that the next line is a continuation of this one.
            bullet_index = index + 1
            stopped = False
            # lookahead N lines to next bullet. Example: 118hres190ih
            while not stopped and bullet_index < line_count and len(lines[bullet_index]) > 0:
                if is_bullet(lines[bullet_index].strip()):
                    stopped = True
                else:
                    line_stripped += lines[bullet_index]
                    bullet_index += 1
                    index += 1
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
            # We compress the text a little by removing some consecutive newlines.
            if empty_line_count < 2 and len(line) < 50:
                html += "<br>"
            if len(line_stripped) == 0:
                empty_line_count += 1
            else:
                empty_line_count = 0
        index += 1
    return html
