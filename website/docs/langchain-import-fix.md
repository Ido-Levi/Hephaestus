# LangChain Import Fix: Restoring Multi-Provider System

## Problem

The multi-provider LLM system was completely broken due to a deprecated import path from LangChain 1.0+. This caused the system to silently fall back to legacy single-provider mode, making Guardian and Conductor monitoring completely non-functional.

### Symptoms
- All Guardian analyses showed "LLM analysis unavailable - using default"
- System called `api.openai.com` with OpenRouter model names (400 errors)
- Agent monitoring produced meaningless 0.5 alignment scores
- No steering interventions, agents getting stuck

### Impact
100% of Guardian analyses (all 2,707+ records) were defaults instead of real LLM-powered trajectory analysis.

## Root Cause

**File:** `src/interfaces/langchain_llm_client.py` (line 14)

LangChain 1.0+ moved the import path but the code wasn't updated:

```diff
- from langchain.schema import Document
+ from langchain_core.documents import Document
```

This single import failure prevented `LangChainLLMClient` from loading, causing silent fallback to `OpenAIProvider` which ignored all OpenRouter + Cerebras configuration.

## The Fix

### Code Change
```python
# File: src/interfaces/langchain_llm_client.py (line 14)
from langchain_core.documents import Document  # Was: from langchain.schema import Document
```

### Configuration
The system was designed to use:
- **Provider:** OpenRouter
- **Routing:** Cerebras (fast inference)
- **Model:** openai/gpt-oss-120b (GPT-4-level reasoning)

This configuration was correct all along - the import bug prevented it from being used.

## Verification

### Before Fix
```
⚠️ Multi-provider config not available, falling back to single provider
⚠️ Using LEGACY SINGLE-PROVIDER mode
HTTP POST https://api.openai.com/v1/chat/completions "HTTP/1.1 400 Bad Request"
```

### After Fix
```
✓ guardian_analysis: openai/gpt-oss-120b [openrouter (via Cerebras)]
✓ conductor_analysis: openai/gpt-oss-120b [openrouter (via Cerebras)]
HTTP POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
```

### Guardian Analysis Quality
**Before:** "LLM analysis unavailable - using default" (alignment: 0.5)

**After:** Real analyses like "Agent has read the PRD and generated requirements analysis, but still needs to create infrastructure tickets..."  (alignment: 0.55-0.75)

## Testing

1. ✅ Import test passes
2. ✅ Multi-provider system loads (5 components configured)
3. ✅ OpenRouter API calls successful (200 OK)
4. ✅ Guardian producing real trajectory analyses
5. ✅ Steering recommendations working
6. ✅ Alignment scores varying naturally

## Impact

This fix restores the entire autonomous monitoring system:
- Guardian can see agent trajectories
- Steering interventions work when agents drift
- Conductor can detect duplicate work
- OpenRouter + Cerebras provides fast, cheap, quality monitoring
- System can self-heal as designed

Without this fix, Hephaestus runs but is completely blind to agent behavior with no intervention capability.
