<?php
class FPDF {
    protected $page = '';
    function __construct(){}
    function SetTitle($t){}
    function SetFont($f,$s,$size){}
    function Ln($h=4){ $this->page .= "\n"; }
    function Cell($w,$h,$txt,$b=0,$ln=0){ $this->page .= $txt; }
    function Output($name='doc.pdf',$dest='D'){
        $content = "GreenPoint - Monthly Report\n\n" . $this->page;
        header('Content-Type: application/pdf');
        header('Content-Disposition: attachment; filename="' . $name . '"');
        echo $content;
        exit;
    }
}
?>