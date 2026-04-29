import markdown
import html
text = "Here is a table tag: <td>\n\n**Bold text**"
escaped = html.escape(text)
html_str = markdown.markdown(escaped)
print(html_str)
