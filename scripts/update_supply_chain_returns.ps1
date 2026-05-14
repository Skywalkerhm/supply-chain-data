$ErrorActionPreference = "Stop"

$dataPath = Join-Path $PSScriptRoot "..\supply_chain_heatmap.json"
$yahooChartBase = "https://query1.finance.yahoo.com/v8/finance/chart"

function Get-PctChange($Latest, $Base) {
  if ($null -eq $Latest -or $null -eq $Base -or [double]$Base -eq 0) {
    return $null
  }
  return [math]::Round((([double]$Latest / [double]$Base) - 1) * 100, 2)
}

function Get-FirstDayUtcMs($TimestampSeconds) {
  $date = [DateTimeOffset]::FromUnixTimeSeconds([int64]$TimestampSeconds).UtcDateTime
  return ([DateTimeOffset]::new($date.Year, $date.Month, 1, 0, 0, 0, [TimeSpan]::Zero)).ToUnixTimeMilliseconds()
}

function Get-Chart($Ticker) {
  $encodedTicker = [uri]::EscapeDataString($Ticker)
  $url = "$yahooChartBase/$encodedTicker" + "?range=ytd&interval=1d"
  $headers = @{
    "User-Agent" = "Mozilla/5.0 semi-hub heatmap updater"
    "Accept" = "application/json"
  }
  $response = Invoke-WebRequest -UseBasicParsing -Uri $url -Headers $headers
  $json = $response.Content | ConvertFrom-Json
  $result = $json.chart.result[0]
  if ($null -eq $result) {
    throw "$Ticker`: missing chart result"
  }
  return $result
}

function Get-Returns($Chart) {
  $timestamps = @($Chart.timestamp)
  $adjcloses = @($Chart.indicators.adjclose[0].adjclose)
  $rows = @()

  for ($i = 0; $i -lt $timestamps.Count; $i++) {
    $close = $adjcloses[$i]
    if ($null -ne $close) {
      $rows += [pscustomobject]@{
        ts = [int64]$timestamps[$i]
        close = [double]$close
      }
    }
  }

  if ($rows.Count -eq 0) {
    return [pscustomobject]@{ mtd_pct = $null; ytd_pct = $null }
  }

  $latest = $rows[-1]
  $monthStartMs = Get-FirstDayUtcMs $latest.ts
  $beforeMonth = @($rows | Where-Object { ($_.ts * 1000) -lt $monthStartMs } | Select-Object -Last 1)
  $mtdBase = if ($beforeMonth.Count -gt 0) { $beforeMonth[0].close } else { $rows[0].close }
  $ytdBase = $Chart.meta.chartPreviousClose

  return [pscustomobject]@{
    mtd_pct = Get-PctChange $latest.close $mtdBase
    ytd_pct = Get-PctChange $latest.close $ytdBase
  }
}

$data = Get-Content -Path $dataPath -Raw -Encoding UTF8 | ConvertFrom-Json
$failures = @()

foreach ($stock in $data.stocks) {
  try {
    $chart = Get-Chart $stock.ticker
    $returns = Get-Returns $chart
    $stock | Add-Member -NotePropertyName "mtd_pct" -NotePropertyValue $returns.mtd_pct -Force
    $stock | Add-Member -NotePropertyName "ytd_pct" -NotePropertyValue $returns.ytd_pct -Force
    Start-Sleep -Milliseconds 150
  } catch {
    $stock | Add-Member -NotePropertyName "mtd_pct" -NotePropertyValue $null -Force
    $stock | Add-Member -NotePropertyName "ytd_pct" -NotePropertyValue $null -Force
    $failures += "$($stock.ticker): $($_.Exception.Message)"
  }
}

$jsonOut = ($data | ConvertTo-Json -Depth 8) + "`n"
[System.IO.File]::WriteAllText((Resolve-Path $dataPath), $jsonOut, [System.Text.UTF8Encoding]::new($false))

if ($failures.Count -gt 0) {
  Write-Warning "Updated with $($failures.Count) failures:"
  $failures | ForEach-Object { Write-Warning $_ }
} else {
  Write-Host "Updated $($data.stocks.Count) stocks with MTD/YTD returns."
}
