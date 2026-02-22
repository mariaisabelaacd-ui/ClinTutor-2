from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font('Helvetica', '', 7)

for i in range(3):
    pdf.cell(30, 6, f'Date {i}', 1, 0, 'C')
    pdf.cell(65, 6, f'Question {i}', 1, 0, 'L')
    pdf.cell(35, 6, 'Comp', 1, 0, 'C')
    pdf.cell(20, 6, 'Status', 1, 0, 'C')
    pdf.cell(20, 6, 'Tempo', 1, 0, 'C')
    pdf.cell(20, 6, 'Pts', 1, 0, 'C')
    pdf.ln()

    ans_text = "a ribose tem um OH ligado..."
    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_x(40) # margin is at 10, shift right by 30
    pdf.multi_cell(160, 5, f'Resposta do Aluno: {ans_text}', border=0, fill=False)
    pdf.set_font('Helvetica', '', 7)
    pdf.set_x(10)

pdf.output('test_pdf.pdf')
print("PDF gerado. Checking coordinates...")
