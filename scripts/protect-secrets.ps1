param([string[]]$PrivatePaths = @('secrets', 'state/backups'))
$ErrorActionPreference = 'Stop'
$projectRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd('\')
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$systemSid = New-Object System.Security.Principal.SecurityIdentifier('S-1-5-18')
foreach ($privatePath in $PrivatePaths) {
    $targetPath = [System.IO.Path]::GetFullPath($(if ([System.IO.Path]::IsPathRooted($privatePath)) { $privatePath } else { Join-Path $projectRoot $privatePath }))
    if (-not $targetPath.StartsWith($projectRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Private ACL target must remain strictly within the project root.' }
    $ancestor = $targetPath
    while ($ancestor -and $ancestor.StartsWith($projectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        if (Test-Path -LiteralPath $ancestor) {
            if ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [System.IO.FileAttributes]::ReparsePoint) { throw 'Refusing ACL changes through a reparse point.' }
        }
        if ($ancestor -eq $projectRoot) { break }
        $ancestor = Split-Path -Parent $ancestor
    }
    if (-not (Test-Path -LiteralPath $targetPath)) { New-Item -ItemType Directory -Path $targetPath | Out-Null }
    $items = @((Get-Item -LiteralPath $targetPath -Force)) + @(Get-ChildItem -LiteralPath $targetPath -Force -Recurse)
    foreach ($item in $items) {
        $resolvedItem = [System.IO.Path]::GetFullPath($item.FullName)
        if ($resolvedItem -ne $targetPath -and -not $resolvedItem.StartsWith($targetPath + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'ACL descendant escaped its checked private target.' }
        if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { throw 'Refusing ACL changes through a reparse point.' }
        if ($item.PSIsContainer) { $acl = New-Object System.Security.AccessControl.DirectorySecurity }
        else { $acl = New-Object System.Security.AccessControl.FileSecurity }
        $acl.SetOwner($identity)
        $acl.SetAccessRuleProtection($true, $false)
        foreach ($sid in @($identity, $systemSid)) {
            if ($item.PSIsContainer) {
                $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($sid, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
            } else { $rule = New-Object System.Security.AccessControl.FileSystemAccessRule($sid, 'FullControl', 'Allow') }
            $acl.AddAccessRule($rule)
        }
        Set-Acl -LiteralPath $item.FullName -AclObject $acl
        $verifiedAcl = Get-Acl -LiteralPath $item.FullName
        if ($verifiedAcl.GetOwner([System.Security.Principal.SecurityIdentifier]) -ne $identity -or -not $verifiedAcl.AreAccessRulesProtected) {
            throw 'Private ACL owner or inheritance protection verification failed.'
        }
        $verifiedRules = @($verifiedAcl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]))
        $verifiedPrincipals = @($verifiedRules | ForEach-Object { $_.IdentityReference.Value } | Sort-Object -Unique)
        $expectedPrincipals = @($identity.Value, $systemSid.Value | Sort-Object -Unique)
        if ($verifiedRules.Count -ne 2 -or
            ($verifiedPrincipals -join ',') -ne ($expectedPrincipals -join ',') -or
            @($verifiedRules | Where-Object {
                $_.AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow -or
                $_.FileSystemRights -ne [System.Security.AccessControl.FileSystemRights]::FullControl
            }).Count -ne 0) {
            throw 'Private ACL principal or permission verification failed.'
        }
    }
}
Write-Host 'Applied and verified private targets restricted to current account and SYSTEM, including existing children.'
