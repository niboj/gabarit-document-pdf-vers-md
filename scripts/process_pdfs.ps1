param(
    [string]$Pdf,
    [switch]$Force
)

$python = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "py" }

$args = @("scripts/process_pdfs.py")
if ($Pdf) {
    $args += @("--pdf", $Pdf)
}
if ($Force) {
    $args += "--force"
}

& $python @args
exit $LASTEXITCODE
