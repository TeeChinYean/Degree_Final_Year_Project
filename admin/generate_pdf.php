<?php
require 'includes/db.php';
require 'fpdf/fpdf.php';

if (!method_exists('FPDF', 'AddPage')) {
    die('FPDF failed to load correctly.');
}

// Query the actual recycle table (joined with item_type for names)
$stmt = $pdo->query("
  SELECT i.Type AS type, 
         SUM(r.count) AS quantity,
         SUM(r.weight) AS weight,
         MIN(r.recycle_date) AS start_date,
         MAX(r.recycle_date) AS end_date
  FROM recycle r
  JOIN item_types i ON r.item_type_id = i.item_id
  GROUP BY i.type
  ORDER BY weight DESC
");
$rows = $stmt->fetchAll();

// Create PDF
$pdf = new FPDF('P', 'mm', 'A4');
$pdf->AddPage();
$pdf->SetTitle('Monthly Report');

$pdf->SetFont('Arial', 'B', 16);
$pdf->Cell(0, 10, 'GreenPoint - Recycle Summary Report', 0, 1, 'C');
$pdf->Ln(6);

// Table headers
$pdf->SetFont('Arial', 'B', 12);
$pdf->SetFillColor(230, 240, 255);
$pdf->Cell(50, 10, 'Type', 1, 0, 'C', true);
$pdf->Cell(30, 10, 'Quantity', 1, 0, 'C', true);
$pdf->Cell(30, 10, 'Weight (kg)', 1, 0, 'C', true);
$pdf->Cell(40, 10, 'Start Date', 1, 0, 'C', true);
$pdf->Cell(40, 10, 'End Date', 1, 1, 'C', true);

// Data
$pdf->SetFont('Arial', '', 11);
foreach ($rows as $r) {
    $pdf->Cell(50, 10, $r['type'], 1, 0, 'C');
    $pdf->Cell(30, 10, $r['quantity'], 1, 0, 'C');
    $pdf->Cell(30, 10, number_format($r['weight'], 2), 1, 0, 'C');
    $pdf->Cell(40, 10, date('Y-m-d', strtotime($r['start_date'])), 1, 0, 'C');
    $pdf->Cell(40, 10, date('Y-m-d', strtotime($r['end_date'])), 1, 1, 'C');
}

$pdf->Ln(10);
$pdf->SetFont('Arial', 'I', 10);
$pdf->Cell(0, 10, 'Generated on ' . date('Y-m-d H:i:s'), 0, 1, 'R');

$pdf->Output('Recycle_Report.pdf', 'D');
?>
