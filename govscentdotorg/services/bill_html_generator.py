def us_bill_text_to_html(text: str) -> str:
    lines = text.splitlines()
    html = ""
    empty_line_count = 0
    for line in lines:
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
            html += f"<h2 class='text-center'>{line_stripped}</h3>"
        elif line_stripped == "<DOC>":
            continue
        elif line_stripped.startswith('(') and line_stripped[2] == ')':
            html += f"<div class='bullet'>{line}</div>"
        elif line_stripped.startswith('``'):
            html += f"<div class='bullet'>{line}</div>"
        else:
            html += line
            # We compress the text a little by removing some consecutive newline.s
            if empty_line_count < 3 and len(line) < 50:
                html += "<br>"
            if len(line_stripped) == 0:
                empty_line_count += 1
            else:
                empty_line_count = 0
    return html
