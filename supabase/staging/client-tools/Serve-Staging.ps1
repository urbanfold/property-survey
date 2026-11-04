# Local static server only. No installs, admin rights, database writes or deployments.
# The execution-policy override in START-STAGING.cmd applies only to that process.
$ErrorActionPreference = 'Stop'
$stagingRoot = $PSScriptRoot
$stagingPort = 8794
$stagingAllowed = @{
    '/index.html' = 'text/html; charset=utf-8'
    '/app.js' = 'text/javascript; charset=utf-8'
    '/configure.js' = 'text/javascript; charset=utf-8'
    '/vendor/html2pdf.bundle.min.js' = 'text/javascript; charset=utf-8'
    '/vendor/jszip.min.js' = 'text/javascript; charset=utf-8'
    '/vendor/supabase.js' = 'text/javascript; charset=utf-8'
    '/test-photo.svg' = 'image/svg+xml'
}
$stagingListener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $stagingPort)
try {
    $stagingListener.Start()
    Write-Host "Urbanfold STAGING only: http://localhost:$stagingPort/"
    Write-Host 'Leave this window open. Close it to stop the local server.'
    Start-Process "http://localhost:$stagingPort/"
    while ($true) {
        $stagingConnection = $stagingListener.AcceptTcpClient()
        try {
            $stagingStream = $stagingConnection.GetStream()
            $stagingStream.ReadTimeout = 3000
            $stagingReader = [System.IO.StreamReader]::new($stagingStream, [System.Text.Encoding]::ASCII, $false, 1024, $true)
            $stagingRequest = $stagingReader.ReadLine()
            if (-not $stagingRequest) { continue }
            $stagingParts = $stagingRequest.Split(' ')
            for ($stagingIndex = 0; $stagingIndex -lt 100; $stagingIndex++) {
                $stagingHeaderLine = $stagingReader.ReadLine()
                if (-not $stagingHeaderLine) { break }
            }
            $stagingPath = $stagingParts[1].Split('?')[0]
            if ($stagingPath -eq '/') { $stagingPath = '/index.html' }
            if (($stagingParts[0] -in @('GET','HEAD')) -and $stagingAllowed.ContainsKey($stagingPath)) {
                $stagingBytes = [System.IO.File]::ReadAllBytes((Join-Path $stagingRoot $stagingPath.TrimStart('/')))
                $stagingType = $stagingAllowed[$stagingPath]
                $stagingCode = '200 OK'
            } else {
                $stagingBytes = [System.Text.Encoding]::UTF8.GetBytes('Not found')
                $stagingType = 'text/plain; charset=utf-8'
                $stagingCode = '404 Not Found'
            }
            $stagingHeader = "HTTP/1.1 $stagingCode`r`nContent-Type: $stagingType`r`nContent-Length: $($stagingBytes.Length)`r`nCache-Control: no-store`r`nConnection: close`r`nX-Content-Type-Options: nosniff`r`n`r`n"
            $stagingHeaderBytes = [System.Text.Encoding]::ASCII.GetBytes($stagingHeader)
            $stagingStream.Write($stagingHeaderBytes, 0, $stagingHeaderBytes.Length)
            if ($stagingParts[0] -ne 'HEAD') { $stagingStream.Write($stagingBytes, 0, $stagingBytes.Length) }
        } catch {
            Write-Host 'An incomplete local browser request was closed; the server is still running.'
        } finally { $stagingConnection.Close() }
    }
} catch {
    Write-Host "Could not start/continue the local staging server: $($_.Exception.Message)"
    Write-Host 'Do not change production settings. Close other staging launchers if port 8794 is occupied.'
} finally { $stagingListener.Stop() }
