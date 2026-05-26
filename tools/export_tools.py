from fpdf import FPDF
import markdown

class PDF(FPDF):
    def header(self):
        # Set font
        self.set_font("helvetica", "B", 15)
        # Title
        self.cell(0, 10, "Stock Analysis Agent - Report", border=0, align="C", new_x="LMARGIN", new_y="NEXT")
        # Line break
        self.ln(10)

    def footer(self):
        # Go to 1.5 cm from bottom
        self.set_y(-15)
        # Set font
        self.set_font("helvetica", "I", 8)
        # Page number
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

def generate_pdf(markdown_content: str) -> bytes:
    """
    Converts raw markdown text directly into a formatted PDF byte stream.
    Uses markdown to HTML parsing, and fpdf2 for HTML rendering.
    """
    # FPDF's default Helvetica font strictly only supports pure latin-1. 
    # We must explicitly map typography characters (like em-dashes and smart quotes) to ASCII equivalents
    # before brutally stripping out any remaining emojis or unsupported Unicode blocks.
    replacements = {
        '—': '-', '–': '-', '“': '"', '”': '"', 
        '‘': "'", '’': "'", '…': '...', '•': '*',
        '\u200b': '', '\xa0': ' '
    }
    safe_markdown = markdown_content
    for k, v in replacements.items():
        safe_markdown = safe_markdown.replace(k, v)
        
    safe_markdown = safe_markdown.encode('latin-1', errors='ignore').decode('latin-1')
    
    import html
    # Defuse any literal HTML tags Claude might generate to prevent FPDF parser crashes
    safe_markdown = html.escape(safe_markdown)
    
    # Convert the agent's safe markdown cleanly to HTML representation
    html_content = markdown.markdown(safe_markdown, extensions=['tables', 'fenced_code'])
    
    # Initialize the PDF Engine
    pdf = PDF()
    pdf.add_page()
    
    try:
        # fpdf2 natively handles basic HTML styling cleanly
        pdf.write_html(html_content)
    except Exception as e:
        # Graceful fallback to pure text if markdown tables are too deeply nested for fpdf2
        print(f"FPDF Table parse fallback triggered: {e}")
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=10)
        pdf.multi_cell(0, 5, safe_markdown)
    
    # Generate the byte stream safely (no temporary files required)
    return bytes(pdf.output())
