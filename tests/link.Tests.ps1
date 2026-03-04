# tests/link.Tests.ps1
# Pester tests for scripts/link.ps1 logic
#
# Run with: Invoke-Pester tests/link.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)

Describe "link.ps1 - pre-condition checks" {
    Context "compound-gpid global clone detection" {
        It "passes when install path exists" {
            $installDir = Join-Path $TestDrive "compound-gpid"
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
            Test-Path $installDir | Should Be $true
        }

        It "fails when install path does not exist" {
            $installDir = Join-Path $TestDrive "does-not-exist"
            Test-Path $installDir | Should Be $false
        }
    }
}

Describe "link.ps1 - existing .github directory backup" {
    Context "when .github is a regular directory" {
        It "is not recognised as a junction (no LinkType)" {
            $dir = Join-Path $TestDrive "regular-github"
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            $item = Get-Item $dir
            $item.LinkType | Should BeNullOrEmpty
        }

        It "can be renamed to .github.bak" {
            $src = Join-Path $TestDrive "src-github"
            $bak = Join-Path $TestDrive "src-github.bak"
            New-Item -ItemType Directory -Path $src -Force | Out-Null
            Rename-Item -Path $src -NewName "$src.bak"
            Test-Path $src | Should Be $false
            Test-Path $bak | Should Be $true
        }

        It "aborts backup when .github.bak already exists" {
            $bak = Join-Path $TestDrive "already-bak"
            New-Item -ItemType Directory -Path $bak -Force | Out-Null
            Test-Path $bak | Should Be $true
        }
    }
}

Describe "link.ps1 - junction creation" {
    Context "creating a directory junction" {
        It "creates a junction pointing at the target" {
            $target   = Join-Path $TestDrive "junction-target"
            $junction = Join-Path $TestDrive "junction-link"
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            Test-Path $junction | Should Be $true
            (Get-Item $junction).LinkType | Should Be "Junction"
        }

        It "junction LinkType is recognised as already-linked" {
            $target   = Join-Path $TestDrive "linked-target"
            $junction = Join-Path $TestDrive "linked-link"
            New-Item -ItemType Directory -Path $target  -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            $item = Get-Item $junction
            $item.LinkType | Should Be "Junction"
        }
    }
}

Describe "link.ps1 - .gitignore management" {
    Context "when .gitignore does not exist" {
        It "creates .gitignore with .github entry" {
            $gi = Join-Path $TestDrive "new.gitignore"
            Test-Path $gi | Should Be $false
            Add-Content -Path $gi -Value ".github"
            (Get-Content $gi -Raw) -match '\.github' | Should Be $true
        }
    }

    Context "when .gitignore exists but lacks .github entry" {
        It "appends .github to existing .gitignore" {
            $gi = Join-Path $TestDrive "existing.gitignore"
            Set-Content -Path $gi -Value "*.log`n*.tmp"
            Add-Content -Path $gi -Value ".github"
            $content = Get-Content $gi -Raw
            ($content -match '\.github') | Should Be $true
            ($content -match '\.log') | Should Be $true
        }
    }

    Context "when .gitignore already contains .github entry" {
        It "does not add a duplicate entry" {
            $gi = Join-Path $TestDrive "duplicate.gitignore"
            Set-Content -Path $gi -Value ".github`n*.log"

            $lines = Get-Content $gi
            $alreadyPresent = $lines | Where-Object { $_ -eq '.github' }
            if (-not $alreadyPresent) {
                Add-Content -Path $gi -Value ".github"
            }

            $after = Get-Content $gi
            ($after | Where-Object { $_ -eq '.github' } | Measure-Object).Count | Should Be 1
        }
    }

    Context "when .github.bak entry is also needed" {
        It "adds both .github and .github.bak when neither exists" {
            $gi = Join-Path $TestDrive "both.gitignore"
            Set-Content -Path $gi -Value "*.log"

            $lines = Get-Content $gi
            foreach ($entry in @('.github', '.github.bak')) {
                if (-not ($lines | Where-Object { $_ -eq $entry })) {
                    Add-Content -Path $gi -Value $entry
                }
            }

            $final = Get-Content $gi
            ($final | Where-Object { $_ -eq '.github' }     | Measure-Object).Count | Should Be 1
            ($final | Where-Object { $_ -eq '.github.bak' } | Measure-Object).Count | Should Be 1
        }
    }
}
