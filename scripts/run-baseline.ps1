# =============================================================
# diet-agent 真实数据基线脚本
# 作用：跑黄金数据集 -> 产生 Trace -> 自动标注 -> 批量评估 -> 落盘报告
# 用法：powershell -ExecutionPolicy Bypass -File scripts\run-baseline.ps1
# 可选：-BaseUrl http://localhost:8080  -UserId 1  -IncludeJudge
# =============================================================
param(
    [string]$BaseUrl = "http://localhost:8080",
    [int]$UserId = 1,
    [switch]$IncludeJudge
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$datasetPath = Join-Path $scriptDir "dataset.json"
$outDir = Join-Path (Split-Path -Parent $scriptDir) "docs"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

$headers = @{ "X-User-Id" = "$UserId" }

function Invoke-Json($Method, $Url, $BodyObj) {
    if ($null -eq $BodyObj) {
        return Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers -TimeoutSec 120
    }
    $json = $BodyObj | ConvertTo-Json -Depth 8
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    return Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers `
        -ContentType "application/json; charset=utf-8" -Body $bytes -TimeoutSec 120
}

$dataset = Get-Content $datasetPath -Raw -Encoding UTF8 | ConvertFrom-Json
$mode = $dataset.sourceMode
$startedAt = (Get-Date).AddSeconds(-10)
$allTraceIds = @()
$convResults = @()

Write-Host "== 开始跑基线：共 $($dataset.conversations.Count) 组对话 ==" -ForegroundColor Cyan

foreach ($conv in $dataset.conversations) {
    Write-Host "--- [$($conv.id)] $($conv.name)" -ForegroundColor Yellow
    # 1) 建会话
    $sess = Invoke-Json "Post" "$BaseUrl/api/v1/diet/sessions" $null
    $sessionId = $sess.sessionId
    Write-Host "    sessionId=$sessionId"

    foreach ($turn in $conv.turns) {
        # 2) 发消息，拿 traceId
        $chatBody = @{ sessionId = $sessionId; message = $turn.message; sourceMode = $mode }
        $resp = Invoke-Json "Post" "$BaseUrl/api/v1/diet/chat" $chatBody
        $traceId = $resp.traceId
        $allTraceIds += $traceId
        Write-Host "    traceId=$traceId  <= $($turn.message)"

        # 3) 自动标注
        if ($traceId) {
            $labelBody = @{
                expectedIntent        = $turn.expectedIntent
                expectedSlots         = $turn.expectedSlots
                expectedClarifyAction = $turn.expectedClarifyAction
                labelNote             = $turn.note
            }
            Invoke-Json "Put" "$BaseUrl/api/v1/diet/debug/traces/$traceId/label" $labelBody | Out-Null
        }
    }
    $convResults += [pscustomobject]@{ id = $conv.id; name = $conv.name; sessionId = $sessionId }
}

$endedAt = (Get-Date).AddSeconds(10)

# 4) 批量评估
Write-Host "== 批量评估（includeLlmJudge=$($IncludeJudge.IsPresent)）==" -ForegroundColor Cyan
$evalBody = @{
    startAt         = $startedAt.ToString("yyyy-MM-ddTHH:mm:ss")
    endAt           = $endedAt.ToString("yyyy-MM-ddTHH:mm:ss")
    includeLlmJudge = [bool]$IncludeJudge.IsPresent
    limit           = 500
}
$report = Invoke-Json "Post" "$BaseUrl/api/v1/diet/evaluations" $evalBody

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$reportPath = Join-Path $outDir "评估报告-$stamp.json"
$report | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportPath -Encoding UTF8

# 5) 打印关键指标
Write-Host ""
Write-Host "==================== 结果 ====================" -ForegroundColor Green
Write-Host ("窗口        : {0} ~ {1}" -f $evalBody.startAt, $evalBody.endAt)
Write-Host ("Trace 数    : {0}，已标注 {1}" -f $report.totalTraces, $report.labeledTraces)
Write-Host ("平均总分    : {0:N2} / 100" -f $report.avgScore)
Write-Host "各指标均值  :"
$report.metricAverages.PSObject.Properties | ForEach-Object {
    "{0,-28} {1}" -f $_.Name, $_.Value
}
Write-Host ("报告已保存  : {0}" -f $reportPath)

# 兼容 PowerShell 5.1：手动写报告路径，供后续追加
Write-Host "LAST_REPORT=$reportPath"
