from fpdf import FPDF
from app.schemas.report import ReportRequest

def generate_complaint_pdf(data: ReportRequest) -> bytes:
    """
    Generate a professional PDF report for an AIVOA complaint using fpdf2.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Fonts
    pdf.set_font("helvetica", "B", 16)
    
    # Header
    pdf.cell(0, 10, "AIVOA Complaint Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 10, "Autonomous Intelligent Voice/Complaint Operations Assistant", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    # Helper to print sections
    def section_header(title: str):
        pdf.set_font("helvetica", "B", 12)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(0, 10, title, fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    def print_row(label: str, value: str | None):
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(60, 8, f"{label}:")
        pdf.set_font("helvetica", "", 10)
        
        display_val = value if value else "N/A"
        
        # Calculate remaining width for the multi_cell
        # w = 0 doesn't always work as expected if we are mid-line in fpdf2
        remaining_width = pdf.epw - 60
        
        # Use multi_cell for the value, and force it to wrap to the next line
        pdf.multi_cell(remaining_width, 8, str(display_val), new_x="LMARGIN", new_y="NEXT")
        
    complaint = data.complaint
    risk = data.risk
    
    # --- Complaint Information ---
    section_header("Complaint Information")
    print_row("Complaint ID", data.complaint_id)
    print_row("Source/Channel", complaint.complaint_source)
    print_row("Complaint Date", str(complaint.complaint_date) if complaint.complaint_date else None)
    pdf.ln(5)
    
    # --- Customer Information ---
    section_header("Customer Information")
    print_row("Customer Name", complaint.customer_name)
    pdf.ln(5)

    # --- Product & Issue Details ---
    section_header("Product & Issue Details")
    print_row("Product Name", complaint.product_name)
    print_row("Strength / Grade", complaint.product_strength_grade)
    print_row("Batch / Lot Number", complaint.batch_lot_number)
    print_row("Manufacturing Date", str(complaint.manufacturing_date) if complaint.manufacturing_date else None)
    print_row("Expiry Date", str(complaint.expiry_date) if complaint.expiry_date else None)
    print_row("Dosage Form", complaint.dosage_form)
    print_row("Affected Quantity", complaint.affected_quantity)
    print_row("Complaint Type", complaint.complaint_type)
    print_row("Detailed Description", complaint.detailed_description)
    pdf.ln(5)
    
    # --- Risk Assessment & CAPA ---
    section_header("Risk Assessment & CAPA")
    if risk:
        print_row("Severity", risk.severity)
        print_row("Occurrence", str(risk.occurrence) if risk.occurrence else None)
        print_row("Detectability", str(risk.detectability) if risk.detectability else None)
        print_row("RPN", str(risk.rpn) if risk.rpn else None)
        print_row("Regulatory Flag", "Yes" if risk.regulatory_flag else "No")
        print_row("Root Cause Hint", risk.root_cause_hint)
        print_row("Recommended Action", risk.recommended_action)
        print_row("CAPA Recommendation", risk.capa_recommendation)
        print_row("AI Reasoning Summary", risk.ai_reasoning_summary)
    else:
        pdf.set_font("helvetica", "I", 10)
        pdf.cell(0, 8, "No risk assessment available for this complaint.", new_x="LMARGIN", new_y="NEXT")
    
    return pdf.output(dest="S")
