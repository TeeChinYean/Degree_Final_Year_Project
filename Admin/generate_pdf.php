<?php
require 'includes/db.php';
require 'fpdf/fpdf.php';

if (!method_exists('FPDF', 'AddPage')) {
    die('FPDF failed to load correctly.');
}

// Time range filter (same as history.php)
$months = isset($_GET['months']) ? (int)$_GET['months'] : 3;
if ($months <= 0) $months = 3;
$start = date('Y-m-d 00:00:00', strtotime("-{$months} months"));

// Aggregate from recycle + item_types (quantity = submissions; weight stored in g -> convert to kg)
$stmt = $pdo->prepare("
  SELECT 
    i.type AS type, 
    COUNT(*) AS quantity,
    (SUM(r.weight) / 1000) AS weight,
    MIN(r.recycle_date) AS start_date,
    MAX(r.recycle_date) AS end_date
  FROM recycle r
  JOIN item_types i ON r.item_type_id = i.item_id
  WHERE r.recycle_date BETWEEN ? AND NOW()
  GROUP BY i.type
  ORDER BY weight DESC
");
$stmt->execute([$start]);
$rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

// Create PDF
$pdf = new FPDF('P', 'mm', 'A4');
$pdf->AddPage();
$pdf->SetTitle('Recycle Summary Report');

$pdf->SetFont('Arial', 'B', 16);
$pdf->Cell(0, 10, 'Green Point - Recycle Summary Report', 0, 1, 'C');
$pdf->SetFont('Arial', '', 11);
$pdf->Cell(0, 7, 'Range: last ' . $months . ' month(s) (from ' . date('Y-m-d', strtotime($start)) . ')', 0, 1, 'C');
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
    $pdf->Cell(50, 10, (string)$r['type'], 1, 0, 'C');
    $pdf->Cell(30, 10, (string)(int)$r['quantity'], 1, 0, 'C');
    $pdf->Cell(30, 10, number_format((float)$r['weight'], 2), 1, 0, 'C');
    $pdf->Cell(40, 10, date('Y-m-d', strtotime((string)$r['start_date'])), 1, 0, 'C');
    $pdf->Cell(40, 10, date('Y-m-d', strtotime((string)$r['end_date'])), 1, 1, 'C');
}

$pdf->Ln(10);
$pdf->SetFont('Arial', 'I', 10);
$pdf->Cell(0, 10, 'Generated on ' . date('Y-m-d H:i:s'), 0, 1, 'R');

$pdf->Output('Recycle_Report.pdf', 'D');
?>
