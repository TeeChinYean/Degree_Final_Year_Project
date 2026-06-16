GreenPoint - XAMPP Package (index + PDF export)
Place this folder in your XAMPP htdocs directory (e.g., C:\xampp\htdocs\greenpoint_site)

Files:
- includes/db.php        : Edit DB credentials if needed (defaults for XAMPP)
- index.php              : Dashboard page (editable quantities/status, Generate Report button)
- generate_pdf.php       : Creates a clean PDF and forces automatic download
- vendor/fpdf.php        : Minimal helper for PDF download (naive plain text content inside .pdf file)

Steps:
1. Start Apache and MySQL in XAMPP.
2. Create database 'greenpoint' and the table 'monthly_report' (use SQL provided earlier).
3. Open http://localhost/greenpoint_site/ to view the dashboard.
4. Click 'Generate Report (PDF)' to download Monthly_Report.pdf automatically.
