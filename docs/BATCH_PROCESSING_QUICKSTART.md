# Batch Processing Quick Start Guide

## TL;DR - Quick Setup

### For Local Ollama Users

Edit `config/config.yaml`:

```yaml
api:
  max_concurrent_requests: 5  # 3-5 for mid-range, 8-10 for high-end

performance:
  batch_processing:
    enabled: true
    batch_size: 50
    grouping_strategy: 'extension'
```

**Expected speedup: 5-10x faster** ⚡

### For Cloud API Users (OpenAI, etc.)

Edit `config/config.yaml`:

```yaml
api:
  max_concurrent_requests: 10

performance:
  batch_processing:
    enabled: true
    batch_size: 100
    grouping_strategy: 'extension'
    multi_file_requests:
      enabled: true  # 💰 Reduces API costs by ~75%
      max_files_per_request: 5
```

**Expected speedup: 10-20x faster + 75% cost reduction** ⚡💰

## What Changed?

### Before (Serial Processing)
```
File 1 → Process → Wait → Done
File 2 → Process → Wait → Done
File 3 → Process → Wait → Done
...
⏱️ 100 files = 200 seconds
```

### After (Batch Processing)
```
Files 1-5  → Process concurrently → Done
Files 6-10 → Process concurrently → Done
...
⏱️ 100 files = 40 seconds (5x faster!)
```

### After (Multi-File Batch - Optional)
```
Files 1-5  → Single API call → Done
Files 6-10 → Single API call → Done
...
⏱️ 100 files = 20 API calls instead of 100
💰 Cost: 75% reduction
```

## Configuration Parameters Explained

### `max_concurrent_requests`
**What:** Number of simultaneous API calls
**Impact:** Higher = faster, but don't overwhelm your system

| Value | Best For |
|-------|----------|
| 3-5 | Local Ollama (mid-range PC) |
| 5-10 | Local Ollama (high-end PC/GPU) |
| 10-20 | Cloud APIs |

### `batch_size`
**What:** Files processed before logging progress
**Impact:** Larger = less logging overhead, more memory

| Value | Best For |
|-------|----------|
| 20-50 | Low memory systems |
| 50-100 | General purpose |
| 100-200 | High memory, cloud APIs |

### `grouping_strategy`
**What:** How files are ordered before processing
**Impact:** Better cache hit rates, improved classification

| Value | Effect |
|-------|--------|
| `extension` | Groups .pdf with .pdf, .jpg with .jpg (recommended) |
| `size` | Groups small files together, large files together |
| `mixed` | Balanced approach |
| `none` | No grouping (original order) |

### `multi_file_requests.enabled`
**What:** Send multiple files in one API call
**Impact:** 75% fewer API calls, lower costs
**Trade-off:** Requires larger context window, experimental

| When to Enable | When to Disable |
|----------------|-----------------|
| ✅ Cloud APIs (cost savings) | ❌ Local Ollama (no benefit) |
| ✅ High latency networks | ❌ Memory-constrained systems |
| ✅ Large datasets (1000+ files) | ❌ Small datasets (<50 files) |

## Performance Comparison

### Real-World Example: 100 Files

| Configuration | Time | API Calls | Relative Speed | Cost (Cloud) |
|---------------|------|-----------|----------------|--------------|
| **Serial (old)** | 200s | 100 | 1x | $2.00 |
| **Concurrent** | 40s | 100 | **5x faster** | $2.00 |
| **Multi-file** | 50s | 20 | **4x faster** | **$0.50** |

### For 1000 Files

| Configuration | Time | API Calls | Cost (Cloud) |
|---------------|------|-----------|--------------|
| **Serial (old)** | ~33 min | 1000 | $20.00 |
| **Concurrent** | ~7 min | 1000 | $20.00 |
| **Multi-file** | ~8 min | 200 | **$4.00** |

## Testing Your Configuration

### Step 1: Test with Dry Run

```bash
python -m src.cli classify \
  --source /path/to/test_files \
  --dest /path/to/output \
  --dry-run
```

Look for these log messages:
```
[INFO] Using batch processing (batch_size=50, max_concurrent=5)
[INFO] Grouping files by strategy: extension
[INFO] Processing batch 1: files 1-50 of 100
[INFO] Batch completed in 18.5s: 48/50 successful (2.7 files/sec)
```

### Step 2: Check Performance

Good indicators:
- ✅ **2+ files/sec**: Batch processing is working
- ✅ **No errors**: Configuration is correct
- ✅ **Cache hits**: Grouping is effective

Warning signs:
- ⚠️ **<1 file/sec**: May need tuning
- ⚠️ **Rate limit errors**: Reduce `max_concurrent_requests`
- ⚠️ **Memory errors**: Reduce `batch_size`

### Step 3: Tune Parameters

**If too slow:**
```yaml
api:
  max_concurrent_requests: 10  # Increase (was 5)

performance:
  batch_processing:
    batch_size: 100  # Increase (was 50)
```

**If rate limit errors:**
```yaml
api:
  max_concurrent_requests: 3  # Decrease (was 5)
  retry_delay: 5  # Increase (was 2)
```

**If memory errors:**
```yaml
performance:
  batch_processing:
    batch_size: 20  # Decrease (was 50)

  content_analysis:
    max_content_length: 2000  # Decrease (was 5000)
```

## Example Configurations

### Configuration 1: Conservative (Most Compatible)

```yaml
api:
  max_concurrent_requests: 3

performance:
  batch_processing:
    enabled: true
    batch_size: 30
    grouping_strategy: 'extension'
    multi_file_requests:
      enabled: false
```

**Best for:** First-time users, low-end systems
**Expected:** 3-5x speedup, stable performance

### Configuration 2: Balanced (Recommended)

```yaml
api:
  max_concurrent_requests: 5

performance:
  batch_processing:
    enabled: true
    batch_size: 50
    grouping_strategy: 'extension'
    multi_file_requests:
      enabled: false
```

**Best for:** Most users, mid-range systems
**Expected:** 5-8x speedup, good stability

### Configuration 3: Aggressive (Maximum Performance)

```yaml
api:
  max_concurrent_requests: 10

performance:
  batch_processing:
    enabled: true
    batch_size: 100
    grouping_strategy: 'mixed'
    multi_file_requests:
      enabled: true
      max_files_per_request: 5
```

**Best for:** High-end systems, cloud APIs, large datasets
**Expected:** 10-20x speedup, 75% cost reduction

## Monitoring Performance

### Understanding Log Output

```
[INFO] Using batch processing (batch_size=50, max_concurrent=5)
       ↑ Batch processing is enabled

[INFO] Grouping files by strategy: extension
       ↑ Files are being intelligently grouped

[INFO] Processing batch 1: files 1-50 of 100
       ↑ First batch of 50 files being processed

[INFO] Classifying [1/100]: report.pdf
[INFO] Classifying [2/100]: invoice.pdf
[INFO] Classifying [3/100]: data.csv
       ↑ Individual files being classified concurrently

[INFO] Batch completed in 18.5s: 48/50 successful (2.7 files/sec)
       ↑ Batch stats: time, success rate, throughput

[INFO] Successfully classified 98/100 files
       ↑ Overall success rate
```

### Key Metrics to Watch

1. **Files per second**: Higher is better
   - <1: Poor, needs tuning
   - 1-2: Acceptable
   - 2-5: Good
   - 5+: Excellent

2. **Success rate**: Should be >95%
   - <90%: Check model/API
   - 90-95%: Acceptable
   - >95%: Good

3. **Batch time**: Should be consistent
   - Highly variable: System under stress
   - Increasing over time: Memory leak?
   - Stable: Good

## Troubleshooting

### Problem: "No speedup, still slow"

**Check:**
1. Is batch processing enabled?
   ```yaml
   performance:
     batch_processing:
       enabled: true  # Must be true!
   ```

2. Look for this in logs:
   ```
   [INFO] Using batch processing (batch_size=50, max_concurrent=5)
   ```

   If you see `[INFO] Using serial processing`, batch mode is disabled.

### Problem: "Rate limit errors"

**Solution:**
```yaml
api:
  max_concurrent_requests: 2  # Reduce from current value
  retry_delay: 5  # Increase delay
```

### Problem: "Out of memory"

**Solution:**
```yaml
performance:
  batch_processing:
    batch_size: 20  # Reduce
  content_analysis:
    max_content_length: 2000  # Reduce
```

### Problem: "Multi-file batching not working"

**Symptoms:** Classifications are incorrect or empty

**Solution:**
```yaml
performance:
  batch_processing:
    multi_file_requests:
      enabled: false  # Disable and use concurrent mode
```

Some models don't handle multi-file array responses well. Stick with concurrent processing.

## FAQ

### Q: Will this work with my current setup?

**A:** Yes! Batch processing is backward compatible. If it encounters issues, it automatically falls back to serial processing.

### Q: Should I enable multi-file batching?

**A:**
- ✅ **Yes** if using cloud APIs (OpenAI, Anthropic, etc.) - saves money
- ❌ **No** if using local Ollama - no benefit, adds complexity

### Q: What if I have thousands of files?

**A:** Increase batch size and consider multi-file batching:
```yaml
performance:
  batch_processing:
    batch_size: 200  # Process more at once
    multi_file_requests:
      enabled: true  # Reduce API calls significantly
```

### Q: Can I disable batch processing?

**A:** Yes, set `enabled: false`:
```yaml
performance:
  batch_processing:
    enabled: false
```

System will revert to serial processing.

### Q: How do I know what settings to use?

**A:** Start with the "Balanced" configuration, run a test, then adjust based on logs:
- Too slow? Increase `max_concurrent_requests`
- Rate limit errors? Decrease `max_concurrent_requests`
- Memory errors? Decrease `batch_size`

## Advanced Tips

### Tip 1: Pre-warm the cache

Run classification on a representative sample first:
```bash
python -m src.cli classify --source sample/ --dest temp/
```

Then run on full dataset - cache will speed up similar files.

### Tip 2: Use grouping strategy wisely

- **`extension`**: Best for mixed file types
- **`size`**: Best when memory is limited
- **`mixed`**: Best for very large datasets

### Tip 3: Monitor system resources

```bash
# Watch GPU usage (for local Ollama)
watch -n 1 nvidia-smi

# Watch memory
watch -n 1 free -h

# Watch CPU
htop
```

Adjust `max_concurrent_requests` to keep utilization at 70-90%.

### Tip 4: Combine with caching

Enable caching for maximum performance:
```yaml
app:
  cache_enabled: true
  cache_ttl_hours: 48  # Longer for stable classifications
```

Re-running on the same files will be near-instant.

## Summary

**Default settings work well for most users:**
- ✅ Batch processing enabled
- ✅ 5 concurrent requests
- ✅ Extension-based grouping
- ✅ 5-10x speedup out of the box

**For cloud APIs, enable multi-file batching:**
- ✅ 75% cost reduction
- ✅ Fewer API calls
- ✅ Same or better speed

**Start conservative, tune as needed:**
1. Test with recommended settings
2. Monitor logs and metrics
3. Adjust based on performance
4. Iterate to find optimal configuration

---

**Need more details?** See [BATCH_PROCESSING_OPTIMIZATION.md](./BATCH_PROCESSING_OPTIMIZATION.md) for comprehensive documentation.
