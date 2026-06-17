# use_F_drive.ps1
# Route ALL large model downloads/caches to F:\ instead of C:\ user profile.
# Run ONCE in PowerShell as Administrator (machine-wide), or omit -Scope for current user.
# After running, open a NEW terminal so the variables take effect.

param([string]$Root = "F:\ai_cache", [switch]$Machine)
$scope = if ($Machine) { "Machine" } else { "User" }

# create the cache folders
$dirs = @("$Root\huggingface", "$Root\torch", "$Root\panns_data", "$Root\audio_separator")
foreach ($d in $dirs) { New-Item -ItemType Directory -Force -Path $d | Out-Null }

# Hugging Face (Qwen2-Audio / Qwen3-Omni, transformers, anything HF) - HF_HOME is the umbrella var
[Environment]::SetEnvironmentVariable("HF_HOME", "$Root\huggingface", $scope)
# PyTorch hub / torchaudio / demucs weights
[Environment]::SetEnvironmentVariable("TORCH_HOME", "$Root\torch", $scope)
# PANNs checkpoint (used by 23_deep_listen.py)
[Environment]::SetEnvironmentVariable("PANNS_DATA_DIR", "$Root\panns_data", $scope)
# audio-separator (BS-RoFormer) model files (11 / 24)
[Environment]::SetEnvironmentVariable("AUDIO_SEPARATOR_MODELS", "$Root\audio_separator", $scope)

Write-Host "Caches routed to $Root (scope: $scope)."
Write-Host "Open a NEW terminal, then verify with:  echo `$env:HF_HOME"
