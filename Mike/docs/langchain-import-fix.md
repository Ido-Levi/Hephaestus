# LangChain Import Fix: Multi-Provider System Restoration

**Date:** 2025-11-02  
**Issue:** Multi-provider LLM system failing to load, falling back to legacy single-provider mode  
**Impact:** Guardian and Conductor monitoring completely blind - using default analyses instead of real LLM insights

---

## Problem Discovery

### Symptoms
1. **Guardian analyses showing 100% defaults**: All 2,707+ Guardian analyses contained "LLM analysis unavailable - using default" instead of real trajectory summaries
2. **System logs showing fallback**: Backend logs repeatedly showing:
   ```
   WARNING - ⚠️ Multi-provider config not available, falling back to single provider: No module named 'langchain.schema'
   INFO - ⚠️ Using LEGACY SINGLE-PROVIDER mode
   ```
3. **Wrong API being called**: System calling `api.openai.com` with OpenRouter model names, causing "invalid model ID" errors
4. **Config ignored**: Despite `hephaestus_config.yaml` specifying OpenRouter + Cerebras, system wasn't using it

### Investigation Path
1. Initially thought model `openai/gpt-oss-120b` was invalid
2. Discovered model exists and works via direct OpenRouter API testing
3. Found config was correct (original design by Ido)
4. Traced issue to multi-provider system not loading
5. Identified import error: `langchain.schema` module not found

---

## Root Cause

### The Bug
**File:** `src/interfaces/langchain_llm_client.py` (line 14)  
**Problem:** Using deprecated import path from older LangChain version

```python
# ❌ OLD (broken in langchain 1.0+)
from langchain.schema import Document

# ✅ NEW (correct for langchain 1.0+)
from langchain_core.documents import Document
```

### Why It Broke
- LangChain underwent major refactoring in 1.0 release
- `langchain.schema` module was moved to `langchain_core` submodules
- Import path changed but code wasn't updated
- Python couldn't import `LangChainLLMClient`, causing fallback to legacy mode

### Cascading Failures
1. **Import fails** → LangChain client unavailable
2. **System falls back** → Uses legacy `OpenAIProvider` only
3. **Config ignored** → Multi-provider assignments not used
4. **Wrong API called** → OpenAI API with OpenRouter model names
5. **Guardian blind** → All analyses use defaults (0.5 alignment score, no steering)

---

## The Fix

### Code Change
**File:** `src/interfaces/langchain_llm_client.py`

```diff
  from langchain_openai import ChatOpenAI, OpenAIEmbeddings
  from langchain_groq import ChatGroq
  from langchain_core.messages import HumanMessage, SystemMessage
  from langchain_core.output_parsers import JsonOutputParser
- from langchain.schema import Document
+ from langchain_core.documents import Document
  from pydantic import BaseModel, Field
```

### Verification
```bash
# Test import works
python3 -c "from src.interfaces.langchain_llm_client import LangChainLLMClient"
# ✅ Success! No import errors
```

---

## Testing Results

### Before Fix
```
⚠️ Multi-provider config not available, falling back to single provider
⚠️ Using LEGACY SINGLE-PROVIDER mode
Provider: openai
Model: openai/gpt-oss-120b  (invalid for OpenAI API!)
```

### After Fix
```
✓ guardian_analysis: openai/gpt-oss-120b [openrouter (via Cerebras)]
✓ conductor_analysis: openai/gpt-oss-120b [openrouter (via Cerebras)]
✓ agent_monitoring: openai/gpt-oss-120b [openrouter (via Cerebras)]
✓ task_enrichment: openai/gpt-oss-120b [openrouter (via Cerebras)]
✓ agent_prompts: openai/gpt-oss-120b [openrouter (via Cerebras)]
```

### API Calls Verified
```bash
# Monitor logs showing correct API
HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
# ✅ Using OpenRouter (not api.openai.com)
```

### Guardian Analyses Working
```sql
-- Before: Default analyses
trajectory_summary: "LLM analysis unavailable - using default"
alignment_score: 0.5 (always)

-- After: Real LLM analyses
trajectory_summary: "Agent has read the PRD and generated a requirements 
                     analysis document, but still needs to create 
                     infrastructure and component tickets..."
alignment_score: 0.62 (varies by actual trajectory)
needs_steering: 1 (real steering recommendations)
```

---

## Original System Design

### Ido's Intended Configuration
The system was **always designed** to use:
- **Provider:** OpenRouter
- **Routing:** Cerebras as preferred provider
- **Model:** `openai/gpt-oss-120b` (GPT-4-level model)
- **Purpose:** Fast, cheap, high-quality reasoning for monitoring

### Why OpenRouter + Cerebras?
1. **Speed:** Cerebras inference ~100x faster than standard GPUs
2. **Cost:** Much cheaper than direct OpenAI API
3. **Reasoning:** The 120b model provides GPT-4-class reasoning needed for trajectory analysis
4. **Routing:** OpenRouter handles provider fallbacks and load balancing

### Configuration Correctness
The backup config (`hephaestus_config.yaml.backup`) was **correct all along**:
```yaml
llm:
  default_provider: openrouter
  default_model: openai/gpt-oss-120b
  default_openrouter_provider: cerebras
  
  model_assignments:
    guardian_analysis:
      provider: openrouter
      openrouter_provider: Cerebras
      model: openai/gpt-oss-120b
```

**We mistakenly changed it** thinking the model was invalid, when actually the import bug prevented the config from being used at all.

---

## Impact Assessment

### Critical System Components Affected
1. **Guardian Agent** - Individual agent trajectory monitoring
2. **Conductor Agent** - System-wide coherence analysis
3. **Agent Monitoring** - Health checks and interventions
4. **Task Enrichment** - PRD analysis and task breakdown
5. **Agent Prompts** - Initial agent instructions

### Production Impact
- **All monitoring was blind** for entire workflow runs
- Agents could get stuck with no real steering
- Duplicates not detected (Conductor couldn't analyze)
- No trajectory-aware interventions
- System running but not self-healing as designed

### User Symptoms
- Tasks taking longer than expected
- Agents stuck at prompts for hours
- No meaningful intervention messages
- Guardian showing "analysis unavailable" in logs

---

## Lessons Learned

### 1. Dependency Version Pinning
**Problem:** LangChain 1.0 broke compatibility  
**Solution:** Pin exact versions in `requirements.txt` or document breaking changes

### 2. Fallback Behavior Can Hide Bugs
**Problem:** System silently fell back to legacy mode  
**Solution:** Add startup checks that fail loudly if multi-provider unavailable

### 3. Test Critical Imports Early
**Problem:** Import failure only discovered during deep debugging  
**Solution:** Add import tests to CI/CD pipeline

### 4. Monitor API Usage
**Problem:** Wrong API being called went unnoticed initially  
**Solution:** Log API endpoints being called, alert on unexpected patterns

---

## Recommendations for PR

### For Maintainer (Ido)
1. **Update CI/CD**: Add import tests for all LLM clients
2. **Fail Fast**: Don't silently fall back to legacy mode - fail with clear error
3. **Startup Validation**: Verify multi-provider loaded correctly at startup
4. **Dependency Pins**: Consider pinning langchain versions to prevent future breakage

### For Users
1. **Check Logs**: Look for "LEGACY SINGLE-PROVIDER mode" warning
2. **Verify Guardian**: Check if analyses show real summaries vs defaults
3. **Monitor API**: Ensure calls going to OpenRouter, not api.openai.com
4. **Update Code**: Pull latest fix from this PR

---

## Fix Verification Checklist

- [x] Import error resolved (`langchain_core.documents` works)
- [x] Multi-provider system loads (`✓` messages in logs)
- [x] OpenRouter API called (https://openrouter.ai/api/v1/)
- [x] Cerebras routing configured (extra_body provider order)
- [x] Guardian producing real analyses (not defaults)
- [x] Conductor analyzing system coherence (200 OK responses)
- [x] Alignment scores varying (not stuck at 0.5)
- [x] Steering recommendations working (needs_steering=1)

---

## Related Issues

This fix resolves the core monitoring blindness issue discovered during workflow debugging. Other related fixes in the PR:
- Monitor grace period (prevents premature agent killing)
- Agent ID validation (MCP tool authorization)
- Single database approach (eliminates split database confusion)

**All fixes are atomic and independent** - this LangChain fix stands alone but complements the other improvements.
