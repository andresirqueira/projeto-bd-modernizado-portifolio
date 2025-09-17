# Script para adicionar banner de demonstração em todas as páginas HTML
$htmlFiles = Get-ChildItem -Path . -Filter "*.html" -Exclude "index.html"

foreach ($file in $htmlFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    
    # Verificar se já tem o banner
    if ($content -notmatch "demo-banner\.js") {
        # Adicionar o script do banner após font-awesome
        if ($content -match '(<link rel="stylesheet" href="https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/[^"]+">)') {
            $newContent = $content -replace '(<link rel="stylesheet" href="https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/[^"]+">)', '$1`n    <script src="static/js/demo-banner.js"></script>'
            Set-Content -Path $file.FullName -Value $newContent -Encoding UTF8
            Write-Host "Banner adicionado em: $($file.Name)"
        } else {
            Write-Host "Não foi possível adicionar banner em: $($file.Name) - estrutura não reconhecida"
        }
    } else {
        Write-Host "Banner já existe em: $($file.Name)"
    }
}

Write-Host "Processo concluído!"
