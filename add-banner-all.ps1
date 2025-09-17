# Script para adicionar banner em todas as páginas HTML que ainda não têm
$htmlFiles = Get-ChildItem -Path . -Filter "*.html" -Exclude "index.html"

foreach ($file in $htmlFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    
    # Verificar se já tem o banner
    if ($content -notmatch "demo-banner\.js") {
        Write-Host "Adicionando banner em: $($file.Name)"
        
        # Tentar diferentes padrões de inserção
        if ($content -match '(<link rel="stylesheet" href="https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/[^"]+">)') {
            $newContent = $content -replace '(<link rel="stylesheet" href="https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/[^"]+">)', '$1`n    <script src="static/js/demo-banner.js"></script>'
        } elseif ($content -match '(<script src="https://cdn\.tailwindcss\.com"></script>)') {
            $newContent = $content -replace '(<script src="https://cdn\.tailwindcss\.com"></script>)', '$1`n    <script src="static/js/demo-banner.js"></script>'
        } elseif ($content -match '(<title>[^<]+</title>)') {
            $newContent = $content -replace '(<title>[^<]+</title>)', '$1`n    <script src="static/js/demo-banner.js"></script>'
        } else {
            Write-Host "  Não foi possível adicionar em: $($file.Name) - estrutura não reconhecida"
            continue
        }
        
        Set-Content -Path $file.FullName -Value $newContent -Encoding UTF8
        Write-Host "  ✅ Banner adicionado com sucesso"
    } else {
        Write-Host "Banner já existe em: $($file.Name)"
    }
}

Write-Host "`nProcesso concluído!"
