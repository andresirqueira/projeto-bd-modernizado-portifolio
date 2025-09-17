# Script para adicionar banner de demonstração em TODOS os arquivos HTML
$htmlFiles = Get-ChildItem -Path . -Filter "*.html"

Write-Host "Adicionando banner de demonstração em todos os arquivos HTML..."
Write-Host "Total de arquivos encontrados: $($htmlFiles.Count)"
Write-Host ""

$addedCount = 0
$alreadyExistsCount = 0
$errorCount = 0

foreach ($file in $htmlFiles) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    
    # Verificar se já tem o banner
    if ($content -match "demo-banner\.js") {
        Write-Host "Banner já existe em: $($file.Name)"
        $alreadyExistsCount++
        continue
    }
    
    Write-Host "Adicionando banner em: $($file.Name)"
    
    try {
        # Tentar diferentes padrões de inserção
        $newContent = $null
        
        # Padrão 1: Após font-awesome
        if ($content -match '(<link rel="stylesheet" href="https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/[^"]+">)') {
            $newContent = $content -replace '(<link rel="stylesheet" href="https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/[^"]+">)', '$1`n    <script src="static/js/demo-banner.js"></script>'
        }
        # Padrão 2: Após tailwindcss
        elseif ($content -match '(<script src="https://cdn\.tailwindcss\.com"></script>)') {
            $newContent = $content -replace '(<script src="https://cdn\.tailwindcss\.com"></script>)', '$1`n    <script src="static/js/demo-banner.js"></script>'
        }
        # Padrão 3: Após title
        elseif ($content -match '(<title>[^<]+</title>)') {
            $newContent = $content -replace '(<title>[^<]+</title>)', '$1`n    <script src="static/js/demo-banner.js"></script>'
        }
        # Padrão 4: Após charset
        elseif ($content -match '(<meta charset="UTF-8">)') {
            $newContent = $content -replace '(<meta charset="UTF-8">)', '$1`n    <script src="static/js/demo-banner.js"></script>'
        }
        # Padrão 5: Após head
        elseif ($content -match '(<head>)') {
            $newContent = $content -replace '(<head>)', '$1`n    <script src="static/js/demo-banner.js"></script>'
        }
        else {
            Write-Host "  Estrutura não reconhecida em: $($file.Name)"
            $errorCount++
            continue
        }
        
        if ($newContent) {
            Set-Content -Path $file.FullName -Value $newContent -Encoding UTF8
            Write-Host "  Banner adicionado com sucesso"
            $addedCount++
        }
    }
    catch {
        Write-Host "  Erro ao processar: $($file.Name) - $($_.Exception.Message)"
        $errorCount++
    }
}

Write-Host ""
Write-Host "RESUMO:"
Write-Host "  Adicionados: $addedCount"
Write-Host "  Já existiam: $alreadyExistsCount"
Write-Host "  Erros: $errorCount"
Write-Host "  Total processados: $($htmlFiles.Count)"
Write-Host ""
Write-Host "Banner posicionado no RODAPE de todas as paginas!"
