# E2E run journal — read-only affect

**Plan:** `C:\Users\arnav\read-only-affect-experiment-plan.md`  
**Locked order:** Step 2 → 3 → 4 → 1 → 5 → 6 → 7  
**Host:** local RTX 3050 6GB, `E2E_LOCAL_SAFE=1` (smaller image-forward budgets; dirs still N=32/16)  
**Completion gate:** `docs/e2e_results.json` has `finished` + log `E2E_COMPLETE` + verified headline

## Guardian events

## Agent checks

### 2026-07-31 02:39 — initial (armed)
- Pipeline relaunched as pid **18880** after first boot process died during `PHASE_A_INSTALL` (~90s); guardian `dead_relaunch` working as designed.
- Hardening live: `E2E_LOCAL_SAFE=1` (n_proj_img=8, n_h_pairs=16, n_delta=16, n_gap=16, n_beh=12), per-layer heartbeats, hang guardian stale=25m.
- 20m agent loop armed (shell pid 14768 / terminal 11140). Stop criterion: `finished` + `E2E_COMPLETE` + verified headline/phases.
- Caveat: local_safe reduces image-forward n; dirs still full 32/16.

### 2026-07-31 02:40 — healthy
- Phases: `A_model`, `B_data` done. Phase C: `r_harmful`/`r_harmless` done → **`a_neg 0/16`** with live layer HB (`a_neg:L3`, ~25s into first image).
- GPU 5827 MiB / 100%. On plan pace for Step2 prep (dirs). Image dirs still the long pole (~4 min/img historically).

### 2026-07-31 02:58 — tick #1 (20m)
- **Alive** pid 18880 (~20m), guardian OK, hb_age=0 (`a_neg:L3` cycling).
- Progress: **`a_neg 4/16`** (~4.5 min/img). Not hung.
- Plan pace: still Phase C dirs (pre-Step2). ETA a_neg finish ~55m, then a_neu ~70m, then D kill switch.
- No intervene. Loop continues.

### 2026-07-31 03:18 — tick #2 (20m)
- **Alive** pid 18880 (~40m), guardian OK, hb_age=3 (`a_neg:L26`), GPU 100%.
- Progress: **`a_neg 8/16`** — halfway; ~4.3 min/img steady.
- Plan pace: Phase C on track. ~35m left on a_neg, then a_neu.
- No intervene.

### 2026-07-31 03:38 — tick #3 (20m)
- **Alive** pid 18880 (~60m), hb fresh (`a_neg:L10`), GPU 100%.
- Progress: **`a_neg 13/16`** — ~15m to finish a_neg, then a_neu.
- Plan pace: Phase C still on track for Step2. No intervene.

### 2026-07-31 03:58 — tick #4 (20m)
- **Alive** pid 18880 (~80m), hb fresh (`a_neu:L29`), GPU 100%.
- Progress: **`a_neg` done** → **`a_neu 1/16`**. ~70m left on a_neu, then validate r → Step2 kill switch.
- Plan pace: Phase C on track. No intervene.

### 2026-07-31 04:18 — tick #5 (20m)
- **Alive** pid 18880 (~100m), hb fresh (`a_neu:L19`).
- Progress: **`a_neu 6/16`** — ~45m left on a_neu, then C_validate_r → D Step2.
- Plan pace: Phase C on track. No intervene.

### 2026-07-31 04:38 — tick #6 (20m)
- **Alive** pid 18880 (~120m), hb fresh (`a_neu:L6`), GPU 100%.
- Progress: **`a_neu 11/16`** — ~20m left, then validate r → Step2.
- Plan pace: Phase C on track. No intervene.

### 2026-07-31 04:58 — tick #7 (20m)
- **Alive** pid 18880 (~140m), hb fresh (`a_neu:L28`), GPU 100%.
- Progress: **`a_neu 15/16`** — finishing last image; next: C_dirs save → C_validate_r → **D Step2 kill switch**.
- Plan pace: Phase C completing on schedule. No intervene.

### 2026-07-31 05:18 — tick #8 (20m)
- **Alive** pid 18880 (~160m), hb fresh, GPU 100%.
- **Milestone:** dirs done (resid median 33628); **`r` validation OK** (0.03→1.00); **Step 2 kill switch running**.
- Kill table: `no_image` refuse=1.00 a⟂=-5891.7 r=20299.4; now `proj_a:neutral 3/8` (~5 min/proj).
- Plan pace: on Step 2 (correct order). local_safe caps helping vs prior hang. No intervene.

### 2026-07-31 05:38 — tick #9 (20m)
- **Alive** pid 18880 (~180m), hb fresh (`mean_proj:L7`).
- Progress: `proj_a:neutral` **7/8** — finishing a⟂ arm; next `proj_r:neutral`, then negative/positive conditions.
- Plan pace: Step 2 mid-table. ~5 min/image-proj steady. No intervene.

### 2026-07-31 05:58 — tick #10 (20m)
- **Alive** pid 18880 (~200m), hb_age=12 (`mean_proj:L23`), GPU 100%.
- Progress: `proj_a:neutral` done → **`proj_r:neutral 2/8`**. Then negative/positive kill-table rows.
- Plan pace: Step 2 mid-table. No intervene.

### 2026-07-31 06:18 — tick #11 (20m)
- **Alive** pid 18880 (~220m), hb fresh, GPU 100%.
- Progress: **`proj_r:neutral 6/8`** — ~10m to finish neutral row, then negative/positive.
- Plan pace: Step 2 mid-table. No intervene.

### 2026-07-31 06:38 — tick #12 (20m)
- **Alive** pid 18880 (~240m), hb fresh, GPU 100%.
- **Neutral row done:** refuse=0.83 a⟂=-4187 r=11420 (vs no_image 1.00 / -5892 / 20299).
- Now: **`proj_a:negative 1/8`**. Then positive → Δproj / decision.
- Plan pace: Step 2 mid-table. No intervene.

### 2026-07-31 06:58 — tick #13 (20m)
- **Alive** pid 18880 (~260m), hb fresh (`mean_proj:L5`).
- Progress: **`proj_a:negative 6/8`** — ~10m then `proj_r:negative`, then positive.
- Plan pace: Step 2 mid-table. No intervene.

### 2026-07-31 07:18 — tick #14 (20m)
- **Alive** pid 18880 (~280m), hb fresh, GPU 100%.
- Progress: `proj_a:negative` done → **`proj_r:negative 2/8`**. Then positive → Δproj / decision.
- Plan pace: Step 2 mid-table. No intervene.

### 2026-07-31 07:38 — tick #15 (20m)
- **Alive** pid 18880 (~300m), hb fresh (`mean_proj:L29`).
- Progress: **`proj_r:negative 6/8`** — ~10m to finish negative row, then positive.
- Plan pace: Step 2 mid-table. No intervene.

### 2026-07-31 07:58 — tick #16 (20m)
- **Alive** pid 18880 (~320m), hb fresh, GPU ~100%.
- **Negative row done:** refuse=1.00 a⟂=-3072 r=10912.
- Now: **`proj_a:positive 2/8`**. Then Δproj / harm axis / kill decision.
- Plan pace: Step 2 late-table. No intervene.

### 2026-07-31 08:18 — tick #17 (20m)
- **Alive** pid 18880 (~340m), hb fresh (`mean_proj:L21`).
- Progress: **`proj_a:positive 6/8`** — ~10m then `proj_r:positive`, then Δproj / kill decision.
- Plan pace: Step 2 late-table. No intervene.

### 2026-07-31 08:38 — tick #18 (20m)
- **Alive** pid 18880 (~360m), hb fresh, GPU 100%.
- Progress: `proj_a:positive` done → **`proj_r:positive 2/8`**. Then Δproj / harm axis / kill decision.
- Plan pace: Step 2 late-table. No intervene.

### 2026-07-31 12:34 — laptop sleep/shutdown recovery
- Machine was down ~08:50–12:32. **Pipeline pid 18880 + guardian survived** (sleep/hibernate, not cold kill). Agent 20m loop died — **re-armed**.
- On wake: `proj_r:positive` sample 4 hit soft timeout (`avg layer >120s at L20`) → skipped; continued at **5/8**. Heartbeats live again.
- Partial kill table preserved: no_image / neutral / negative done; positive r-proj finishing.
- No full restart needed. Loop continues to E2E_COMPLETE.

### 2026-07-31 12:39 — tick #19 (post-resume)
- **Alive** pid 18880 (~10h wall), hb fresh (`mean_proj:L21`), GPU 100%.
- Progress: still **`proj_r:positive 5/8`** (mid-forward after wake skip). Kill table incomplete for positive.
- Agent loop pid 9580 confirmed. No intervene.

### 2026-07-31 12:55 — tick #20 (re-armed loop)
- **Alive** pid 18880 (~10.3h), hb fresh (`h_img:L25`), GPU 100%.
- **Kill table complete:** positive refuse=0.92 a⟂=-4010 r=11297.
- Now: harm-axis build — `h_text` done → **`h_img 0/16`**. Then Δproj → **KILL_SWITCH_DECISION**.
- Plan pace: late Step 2. No intervene.

### 2026-07-31 12:59 — tick (stale loop echo)
- Still healthy; **`h_img 1/16`**. ~4–5 min/img → ~1h for h_img then Δproj/decision. No intervene.

### 2026-07-31 13:15 — tick #21
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`h_img 4/16`**. ~1h to Δproj / kill decision. No intervene.

### 2026-07-31 13:35 — tick #22
- **Alive** pid 18880, hb fresh (`h_img:L0`), GPU 100%.
- Progress: **`h_img 7/16`** (~6 min/img). ~55m to Δproj / kill decision. No intervene.

### 2026-07-31 13:55 — tick #23
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`h_img 11/16`**. ~25m to Δproj / kill decision. No intervene.

### 2026-07-31 14:15 — tick #24
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`h_img 15/16`** — last image finishing; next Δproj arms → **KILL_SWITCH_DECISION**.
- Plan pace: end of Step 2. No intervene.

### 2026-07-31 14:35 — tick #25
- **Alive** pid 18880, hb fresh (`delta_img_a:L13`), GPU 100%.
- Progress: `h_img` done → **`delta_img_a 2/16`** (affect Δproj). Then neu/harm Δproj → decision → beh arm.
- Plan pace: late Step 2. No intervene.

### 2026-07-31 14:55 — tick #26
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`delta_img_a 6/16`**. ~50m+ for remaining Δproj arms then kill decision.
- Plan pace: late Step 2. No intervene.

### 2026-07-31 15:15 — tick #27
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`delta_img_a 9/16`**. ~35m to finish this arm, then neu/harm Δproj → kill decision.
- Plan pace: late Step 2. No intervene.

### 2026-07-31 15:19 — tick (stale loop echo)
- Still healthy; **`delta_img_a 10/16`**. No intervene.

### 2026-07-31 15:35 — tick #28
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`delta_img_a 14/16`** — nearly done; then neu_img_a / harm Δproj → **KILL_SWITCH_DECISION**.
- Plan pace: late Step 2. No intervene.

### 2026-07-31 15:55 — tick #29
- **Alive** pid 18880, hb fresh (`neu_img_a:L11`), GPU 100%.
- Progress: `delta_img_a` **done** → **`neu_img_a 2/16`**. Then harm Δproj → kill decision → beh.
- Plan pace: late Step 2. No intervene.

### 2026-07-31 16:15 — tick #30
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`neu_img_a 6/16`**. ~50m for remaining neu/harm Δproj then kill decision.
- Plan pace: late Step 2. No intervene.

### 2026-07-31 16:35 — tick #31
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`neu_img_a 10/16`**. ~30m to finish neu, then harm Δproj → kill decision.
- Plan pace: late Step 2. No intervene.

### 2026-07-31 16:55 — tick #32
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`neu_img_a 14/16`** — nearly done; then harm Δproj → **KILL_SWITCH_DECISION**.
- Plan pace: late Step 2. No intervene.

### 2026-07-31 17:15 — tick #33
- **Alive** pid 18880, hb fresh (`harm_img_h:L27`), GPU busy.
- Progress: `neu_img_a` **done** → **`harm_img_h 2/16`**. Then neu_img_h → ratios → **KILL_SWITCH_DECISION** → beh.
- Plan pace: late Step 2. No intervene.

### 2026-07-31 17:35 — tick #34
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`harm_img_h 7/16`**. ~40m to finish harm + neu_img_h then kill decision.
- Plan pace: late Step 2. No intervene.

### 2026-07-31 17:55 — tick #35
- **Alive** pid 18880, hb fresh, GPU busy.
- Progress: **`harm_img_h 11/16`**. ~25m to finish harm + neu_img_h then kill decision.
- Plan pace: late Step 2. No intervene.

### 2026-07-31 18:15 — tick #36
- **Alive** pid 18880, hb fresh (`neu_img_h:L11`), GPU 100%.
- Progress: `harm_img_h` **done** → **`neu_img_h 0/16`** (last Δproj arm). Then **KILL_SWITCH_DECISION** → beh → Steps 3+.
- Plan pace: end of Step 2 measurements. No intervene.

### 2026-07-31 18:35 — tick #37
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`neu_img_h 4/16`**. ~50m to kill decision.
- Plan pace: end of Step 2 measurements. No intervene.

### 2026-07-31 18:55 — tick #38
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`neu_img_h 9/16`**. ~30m to **KILL_SWITCH_DECISION**.
- Plan pace: end of Step 2 measurements. No intervene.

### 2026-07-31 19:15 — tick #39
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`neu_img_h 14/16`** — ~10m to **KILL_SWITCH_DECISION**, then beh arm / Steps 3+.
- Plan pace: end of Step 2 measurements. No intervene.

### 2026-07-31 19:35 — tick #40 **KILL DECISION**
- **Alive** pid 18880; behavioral arm running (`beh:neutral`).
- **KILL_SWITCH_DECISION=`INCONCLUSIVE_OR_MIXED`** @ 19:24:28
  - Δproj a⟂: txt=15.88 img=3047.62 → **ratio_img/txt=191.92** (images >> text on a⟂ — opposite of Charlotte null; likely solid-color / 4-bit / local_safe artifact)
  - Δproj harm: txt=3052.18 img=-1177.53 → **ratio_img/txt=0.386** (>0.30 harm threshold)
  - Rule needs ratio_a<0.05 AND ratio_h>0.30 for PASS_AFFECT_SPECIFIC → not met → INCONCLUSIVE (pipeline continues, not STOP)
- Beh so far: no_image refuse **0.96**; negative **0.42**; neutral in progress.
- Caveats: solid-color affect proxies, NF4, reduced n — **not paper-grade**; Colab T4 + EMOTIC still required for claims.
- Plan pace: Step 2 decision done → finishing beh → Steps 3→4→1→5→7 (6 skip). No intervene.

### 2026-07-31 19:39 — tick (stale loop) Step 3 started
- `D_step2` persisted. Beh final: no_image **0.96**, negative **0.42**, neutral **0.17**.
- Now **PHASE_E_STEP3_GAP** — `caption 1/16`. On plan pace (2→3). No intervene.

### 2026-07-31 19:55 — tick #41 Step 3
- **Alive** pid 18880, hb fresh (`gap_img:L12`), GPU 100%.
- Captions **done** → **`gap_img 2/16`** (then gap_neu → gap_ratio). On plan pace Step 3. No intervene.

### 2026-07-31 20:15 — tick #42 Step 3
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`gap_img 6/16`**. ~45m to gap_neu + gap_ratio → Step 4. No intervene.

### 2026-07-31 20:35 — tick #43 Step 3
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`gap_img 11/16`**. ~25m to gap_neu + gap_ratio → Step 4. No intervene.

### 2026-07-31 20:55 — tick #44 Step 3
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`gap_img 15/16`** — finishing; next gap_neu → gap_ratio → Step 4.
- Plan pace: late Step 3. No intervene.

### 2026-07-31 20:59 — tick (stale loop)
- `gap_img` **done** → **`gap_neu 0/16`** (mid L24). ~70m to gap_ratio → Step 4. No intervene.

### 2026-07-31 21:15 — tick #45 Step 3
- **Alive** pid 18880, hb fresh, GPU busy.
- Progress: **`gap_neu 4/16`**. ~55m to gap_ratio → Step 4. No intervene.

### 2026-07-31 21:35 — tick #46 Step 3
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`gap_neu 8/16`**. ~35m to gap_ratio → Step 4. No intervene.

### 2026-07-31 21:39 — duplicate tick (loop 11140)
- Still **alive**; **`gap_neu 9/16`**. No intervene.

### 2026-07-31 21:55 — tick #47 Step 3
- **Alive** pid 18880, hb fresh, GPU 100%.
- Progress: **`gap_neu 12/16`**. ~20m to gap_ratio → Step 4. No intervene.

### 2026-07-31 21:59 — duplicate tick (loop 11140)
- Still **alive**; **`gap_neu 12/16`** (hb `gap_neu:L31`). No intervene.

### 2026-07-31 22:15 — tick #48 Step 3→4
- **Alive** pid 18880. **`E_step3` persisted.**
- `gap_ratio |d_cap/d_img| = 0.33` (d_cap=-1015.7, d_img=3047.6) — captions ≪ image deltas (local solid-color caveat; continue).
- **Step 4 started:** `gamma=1` refuse=1.00 rand=1.00 coherent=False. Sweeping remaining γ. No intervene.

### 2026-07-31 22:19 — duplicate tick (loop 11140) Step 4→5
- **`F_step4` complete.** Refuse flips 1.0→0.0 between γ=10 and γ=20; all `coherent=False` (rand refuse stays 1.0).
- Log: `PHASE_G_STEP5_LAYERS` underway (hb `resid:L12`). Alive, GPU 100%. No intervene.

### 2026-07-31 22:35 — tick #49 Step 5
- **Alive** pid 18880, hb fresh (`resid:L30`), GPU 100%.
- Still in **Step 5 layer sweep**; `G_step5` not persisted yet. Then H→I(skip)→J. No intervene.

### 2026-07-31 22:39 — duplicate tick (loop 11140)
- Still **alive**; Step 5 (hb `resid:L21`). No intervene.

### 2026-07-31 22:55 — tick #50 Step 5
- **Alive** pid 18880, hb fresh (`resid:L8`), GPU 100%. ~38m into Step 5 layer sweep; no new log lines yet (progress via HB). Then H→I(skip)→J. No intervene.

### 2026-07-31 22:59 — duplicate tick (loop 11140)
- Still **alive**; Step 5 (hb `resid:L28`). No layer-curve log yet. No intervene.

### 2026-07-31 23:15 — tick #51 Step 5
- **Alive** pid 18880, hb fresh (`resid:L15`, elapsed~107s/forward), GPU 100%.
- ~58m into Step 5; still no `layer N:` log (first sampled layer still computing img/txt Δs). Continue; H→J after. No intervene.

### 2026-07-31 23:19 — duplicate tick (loop 11140)
- Still **alive**; Step 5 (hb `resid:L0`). No intervene.

### 2026-07-31 23:35 — tick #52 Step 5
- **Alive** pid 18880. First curve point landed: **`layer 0: imgΔ=6.97 txtΔ=-3.48`**.
- `G_step5` partial persisted (`layers_sampled=[0]`). Remaining sampled layers 5…30 (~every 5th). Then H→J. No intervene.

### 2026-07-31 23:39 — duplicate tick (loop 11140)
- Still **alive**; layer 0 done, working next sample (hb `resid:L23`). No intervene.

### 2026-07-31 23:55 — tick #53 Step 5
- **Alive** pid 18880, hb fresh (`resid:L15`), GPU 100%.
- Still **1/7** sampled layers (`layers_sampled=[0]`); computing layer 5 (~1h/point on 3050). No intervene.

### 2026-07-31 23:59 — duplicate tick (loop 11140)
- Still **alive**; layers=[0], hb `resid:L32`. No intervene.

### 2026-08-01 00:15 — tick #54 Step 5
- **Alive** pid 18880, hb fresh (`resid:L12`), GPU 100%.
- Still **1/7** (`layers_sampled=[0]`); ~40m into next sampled layer. No intervene.

### 2026-08-01 00:19 — duplicate tick (loop 11140)
- Still **alive**; layers=[0], hb `resid:L26`. No intervene.

### 2026-08-01 00:35 — tick #55 Step 5
- **Alive** pid 18880, hb fresh (`resid:L12`), GPU 100%.
- Still **1/7** (`layers_sampled=[0]`); ~60m into layer-5 point (ETA soon if ~78m like L0). No intervene.

### 2026-08-01 00:39 — duplicate tick (loop 11140)
- Still **alive**; layers=[0], hb `resid:L5`. No intervene.

### 2026-08-01 00:55 — tick #56 Step 5
- **Alive** pid 18880, hb fresh (`resid:L28`), GPU 100%.
- Still **1/7** (`layers_sampled=[0]`); ~80m into next point (L0 was ~78m — late but HB moving). No intervene.

### 2026-08-01 00:59 — duplicate tick (loop 11140) Step 5
- **layer 5 landed** @ 00:56: imgΔ=298.33 txtΔ=7.80. `layers_sampled=[0,5]` (**2/7**).
- Alive, GPU busy on next point. No intervene.

### 2026-08-01 01:15 — tick #57 Step 5
- **Alive** pid 18880, hb fresh (`resid:L21`), GPU 100%.
- Still **2/7** (`[0,5]`); ~19m into layer-10 point. No intervene.

### 2026-08-01 01:19 — duplicate tick (loop 11140)
- Still **alive**; layers=[0,5], hb `resid:L11`. No intervene.

### 2026-08-01 01:35 — tick #58 Step 5
- **Alive** pid 18880, hb fresh (`resid:L7`), GPU 100%.
- Still **2/7** (`[0,5]`); ~39m into layer-10 point. No intervene.

### 2026-08-01 01:39 — duplicate tick (loop 11140)
- Still **alive**; layers=[0,5], hb `resid:L2`. No intervene.

### 2026-08-01 01:55 — tick #59 Step 5
- **Alive** pid 18880, hb fresh (`resid:L21`), GPU 100%.
- Still **2/7** (`[0,5]`); ~59m into layer-10 point (L5 was ~81m). No intervene.

### 2026-08-01 01:59 — duplicate tick (loop 11140)
- Still **alive**; layers=[0,5], hb `resid:L5`. No intervene.

### 2026-08-01 02:15 — tick #60 Step 5
- **Alive** pid 18880. **layer 10 landed** @ 02:12: imgΔ=831.92 txtΔ=26.01.
- `layers_sampled=[0,5,10]` (**3/7**). Rising imgΔ trend. Next point underway. No intervene.

### 2026-08-01 02:19 — duplicate tick (loop 11140)
- Still **alive**; layers=[0,5,10], hb `resid:L14`. No intervene.

### 2026-08-01 02:35 — tick #61 Step 5
- **Alive** pid 18880, hb fresh (`resid:L5`), GPU 100%.
- Still **3/7** (`[0,5,10]`); ~23m into layer-15 point. No intervene.

### 2026-08-01 02:39 — duplicate tick (loop 11140)
- Still **alive**; layers=[0,5,10], hb `resid:L33`. No intervene.

### 2026-08-01 02:55 — tick #62 Step 5
- **Alive** pid 18880, hb fresh (`resid:L26`), GPU 100%.
- Still **3/7** (`[0,5,10]`); ~43m into layer-15 point. No intervene.

### 2026-08-01 02:59 — duplicate tick (loop 11140)
- Still **alive**; layers=[0,5,10], hb `resid:L2` (age~22s). GPU 100%. No intervene.

### 2026-08-01 03:15 — tick #63 Step 5
- **Alive** pid 18880, hb fresh (`resid:L13`), GPU 100%.
- Still **3/7** (`[0,5,10]`); ~63m into layer-15 point. No intervene.

### 2026-08-01 03:19 — duplicate tick (loop 11140)
- Still **alive**; layers=[0,5,10], hb `resid:L4`. No intervene.

### 2026-08-01 03:35 — tick #64 Step 5
- **Alive** pid 18880. **layer 15 landed** @ 03:29: imgΔ=1777.12 txtΔ=-43.78.
- `layers_sampled=[0,5,10,15]` (**4/7**). Strong rising imgΔ. Next point underway. No intervene.

### 2026-08-01 03:39 — duplicate tick (loop 11140)
- Still **alive**; layers=[0,5,10,15], hb `resid:L2`. No intervene.

### 2026-08-01 03:55 — tick #65 Step 5
- **Alive** pid 18880, hb fresh (`resid:L26`), GPU 100%.
- Still **4/7** (`[0,5,10,15]`); ~26m into layer-20 point. No intervene.

### 2026-08-01 03:59 — duplicate tick (loop 11140)
- Still **alive**; layers=[0,5,10,15], hb `resid:L18`. No intervene.

### 2026-08-01 04:15 — tick #66 Step 5
- **Alive** pid 18880, hb fresh (`resid:L20`), GPU 100%.
- Still **4/7** (`[0,5,10,15]`); ~46m into layer-20 point. No intervene.

### 2026-08-01 04:19 — duplicate tick (loop 11140)
- Still **alive**; layers=[0,5,10,15], hb `resid:L4` (VRAM ~4GB — likely text-side forwards). No intervene.

### 2026-08-01 04:35 — tick #67 Step 5
- **Alive** pid 18880, hb fresh (`resid:L27`), GPU busy.
- Still **4/7** (`[0,5,10,15]`); ~66m into layer-20 point. No intervene.

### 2026-08-01 04:39 — duplicate tick (loop 11140)
- Still **alive**; layers=[0,5,10,15], hb `resid:L20`. No intervene.

### 2026-08-01 04:55 — tick #68 Step 5
- **Alive** pid 18880. **layer 20 landed** @ 04:46: imgΔ=2683.87 txtΔ=-121.08.
- `layers_sampled=[0,5,10,15,20]` (**5/7**). Rising imgΔ continues. Next: 25, 30 → H→J. No intervene.

### 2026-08-01 04:59 — duplicate tick (loop 11140)
- Still **alive**; layers=[0,5,10,15,20], hb `resid:L1`. No intervene.

### 2026-08-01 05:15 — tick #69 Step 5
- **Alive** pid 18880, hb fresh (`resid:L16`), GPU 100%.
- Still **5/7** (`[0…20]`); ~29m into layer-25 point. Then 30 → H→J. No intervene.

### 2026-08-01 05:19 — duplicate tick (loop 11140)
- Still **alive**; layers=[0…20], hb `resid:L29`. No intervene.

### 2026-08-01 05:35 — tick #70 Step 5
- **Alive** pid 18880, hb fresh (`resid:L12`), GPU 100%.
- Still **5/7** (`[0…20]`); ~49m into layer-25 point. No intervene.

### 2026-08-01 05:39 — duplicate tick (loop 11140)
- Still **alive**; layers=[0…20], hb `resid:L5`. No intervene.

### 2026-08-01 05:55 — tick #71 Step 5
- **Alive** pid 18880, hb fresh (`resid:L23`), GPU 100%.
- Still **5/7** (`[0…20]`); ~69m into layer-25 point. No intervene.

### 2026-08-01 05:59 — duplicate tick (loop 11140)
- Still **alive**; layers=[0…20], hb `resid:L14` (age~22s). No intervene.

### 2026-08-01 06:15 — tick #72 Step 5
- **Alive** pid 18880. **layer 25 landed** @ 06:02: imgΔ=5340.62 txtΔ=92.26.
- `layers_sampled=[0…25]` (**6/7**). Final point L30 next → H→I(skip)→J. No intervene.

### 2026-08-01 06:19 — duplicate tick (loop 11140)
- Still **alive**; layers=[0…25], hb `resid:L26` (final L30 point). No intervene.

### 2026-08-01 06:35 — tick #73 Step 5
- **Alive** pid 18880, hb fresh (`resid:L19`), GPU busy (~4GB VRAM — text-side).
- Still **6/7** (`[0…25]`); ~33m into final L30 point. Then H→J. No intervene.

### 2026-08-01 06:39 — duplicate tick (loop 11140)
- Still **alive**; layers=[0…25], hb `resid:L5` (final L30). No intervene.

### 2026-08-01 06:55 — tick #74 Step 5
- **Alive** pid 18880, hb fresh (`resid:L20`), GPU 100%.
- Still **6/7** (`[0…25]`); ~53m into final L30 point. Then H→J → E2E_COMPLETE. No intervene.

### 2026-08-01 06:59 — duplicate tick (loop 11140)
- Still **alive**; layers=[0…25], hb `resid:L6` (final L30). No intervene.

### 2026-08-01 07:15 — tick #75 Step 5
- **Alive** pid 18880, hb fresh (`resid:L21`), GPU 100%.
- Still **6/7** (`[0…25]`); ~73m into final L30 (near usual ~76–81m). Then H→J. No intervene.

### 2026-08-01 07:19 — duplicate tick (loop 11140)
- Still **alive**; layers=[0…25], hb `resid:L33` (age~38s — late in forward). No intervene.

### 2026-08-01 07:35 — FINAL: E2E_COMPLETE verified
- Pipeline exited cleanly. `finished=2026-08-01 07:28:32`. Log has `E2E_COMPLETE`.
- Phases present: A,B,C,C_validate_r,D_step2,E,F,G,H,I(skipped),J.
- **Checklist**
  - [x] `finished` set
  - [x] `E2E_COMPLETE` in log
  - [x] `D_step2.decision=INCONCLUSIVE_OR_MIXED`
  - [x] E/F/G/H/J present; I skipped (`local_3050_VRAM_skip_after_gemma`)
  - [x] headline: kill_switch, ratio_a=191.92, ratio_h=0.386, gap_ratio=0.333 (all finite)
  - [x] `C_validate_r`: harmless 0.031 → 1.00 (r works)
  - [x] No NaN in key ratios
- **Headline science (local caveats — not paper-grade)**
  - Kill: `INCONCLUSIVE_OR_MIXED` (a⟂ img≫txt opposite Charlotte; harm img/txt &lt;1)
  - Gap |d_cap/d_img|=0.33; Step4 refuse flips 1→0 between γ=10–20, all coherent=False
  - Step5 imgΔ rises with depth (6.97→7221.74); contagion emo=neu=0 (solid-color/proxy fail)
- Stopped 20m agent loops + guardian. Results: `docs/e2e_results.json`.


- 2026-07-31 02:36:50 guardian_start stale_sec=1500 max_restarts=4 local_safe=1
- 2026-07-31 02:36:53 launch reason=initial restart=1
- 2026-07-31 02:36:53 launched pid=18844
- 2026-07-31 02:36:53 RUNNING pid=18844 hb_age_s=999999 stage=? :: 
- 2026-07-31 02:36:53 HANG_DETECTED pid=18844 hb_age_s=999999 - killing
- 2026-07-31 02:36:59 launch reason=hang_restart age=999999 restart=2
- 2026-07-31 02:36:59 launched pid=28848
- 2026-07-31 02:37:32 guardian_start stale_sec=1500 max_restarts=4 local_safe=1
- 2026-07-31 02:37:35 launch reason=initial restart=1
- 2026-07-31 02:37:35 launched pid=2812
- 2026-07-31 02:39:06 pipeline_dead unfinished - relaunch
- 2026-07-31 02:39:09 launch reason=dead_relaunch restart=2
- 2026-07-31 02:39:09 launched pid=18880
- 2026-07-31 02:41:09 RUNNING pid=18880 hb_age_s=1 stage=a_neg:L6 :: [02:40:14] a_neg 0/16 | [02:40:14] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 02:43:10 RUNNING pid=18880 hb_age_s=2 stage=a_neg:L21 :: [02:40:14] a_neg 0/16 | [02:40:14] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 02:45:10 RUNNING pid=18880 hb_age_s=0 stage=a_neg:L2 :: [02:44:53] a_neg 1/16 | [02:44:53] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 02:47:10 RUNNING pid=18880 hb_age_s=4 stage=a_neg:L16 :: [02:44:53] a_neg 1/16 | [02:44:53] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 02:49:10 RUNNING pid=18880 hb_age_s=6 stage=a_neg:L30 :: [02:44:53] a_neg 1/16 | [02:44:53] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 02:51:10 RUNNING pid=18880 hb_age_s=7 stage=a_neg:L10 :: [02:49:38] a_neg 2/16 | [02:49:38] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 02:53:11 RUNNING pid=18880 hb_age_s=4 stage=a_neg:L25 :: [02:49:38] a_neg 2/16 | [02:49:38] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 02:55:11 RUNNING pid=18880 hb_age_s=2 stage=a_neg:L7 :: [02:54:15] a_neg 3/16 | [02:54:15] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 02:57:11 RUNNING pid=18880 hb_age_s=2 stage=a_neg:L23 :: [02:54:15] a_neg 3/16 | [02:54:15] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 02:59:11 RUNNING pid=18880 hb_age_s=7 stage=a_neg:L4 :: [02:58:33] a_neg 4/16 | [02:58:33] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:01:11 RUNNING pid=18880 hb_age_s=5 stage=a_neg:L20 :: [02:58:33] a_neg 4/16 | [02:58:33] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:03:12 RUNNING pid=18880 hb_age_s=6 stage=a_neg:L2 :: [03:02:51] a_neg 5/16 | [03:02:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:05:12 RUNNING pid=18880 hb_age_s=5 stage=a_neg:L18 :: [03:02:51] a_neg 5/16 | [03:02:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:07:12 RUNNING pid=18880 hb_age_s=4 stage=a_neg:L0 :: [03:07:07] a_neg 6/16 | [03:07:07] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:09:12 RUNNING pid=18880 hb_age_s=3 stage=a_neg:L16 :: [03:07:07] a_neg 6/16 | [03:07:07] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:11:13 RUNNING pid=18880 hb_age_s=3 stage=a_neg:L32 :: [03:07:07] a_neg 6/16 | [03:07:07] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:13:13 RUNNING pid=18880 hb_age_s=2 stage=a_neg:L14 :: [03:11:24] a_neg 7/16 | [03:11:24] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:15:13 RUNNING pid=18880 hb_age_s=2 stage=a_neg:L30 :: [03:11:24] a_neg 7/16 | [03:11:24] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:17:13 RUNNING pid=18880 hb_age_s=1 stage=a_neg:L12 :: [03:15:41] a_neg 8/16 | [03:15:41] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:19:13 RUNNING pid=18880 hb_age_s=7 stage=a_neg:L27 :: [03:15:41] a_neg 8/16 | [03:15:41] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:21:14 RUNNING pid=18880 hb_age_s=4 stage=a_neg:L9 :: [03:20:00] a_neg 9/16 | [03:20:00] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:23:14 RUNNING pid=18880 hb_age_s=0 stage=a_neg:L25 :: [03:20:00] a_neg 9/16 | [03:20:00] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:25:14 RUNNING pid=18880 hb_age_s=3 stage=a_neg:L6 :: [03:24:24] a_neg 10/16 | [03:24:24] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:27:14 RUNNING pid=18880 hb_age_s=7 stage=a_neg:L21 :: [03:24:24] a_neg 10/16 | [03:24:24] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:29:14 RUNNING pid=18880 hb_age_s=2 stage=a_neg:L3 :: [03:28:48] a_neg 11/16 | [03:28:48] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:31:15 RUNNING pid=18880 hb_age_s=6 stage=a_neg:L18 :: [03:28:48] a_neg 11/16 | [03:28:48] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:33:15 RUNNING pid=18880 hb_age_s=2 stage=a_neg:L0 :: [03:33:13] a_neg 12/16 | [03:33:13] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:35:15 RUNNING pid=18880 hb_age_s=5 stage=a_neg:L15 :: [03:33:13] a_neg 12/16 | [03:33:13] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:37:15 RUNNING pid=18880 hb_age_s=1 stage=a_neg:L31 :: [03:33:13] a_neg 12/16 | [03:33:13] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:39:15 RUNNING pid=18880 hb_age_s=4 stage=a_neg:L12 :: [03:37:37] a_neg 13/16 | [03:37:37] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:41:16 RUNNING pid=18880 hb_age_s=0 stage=a_neg:L28 :: [03:37:37] a_neg 13/16 | [03:37:37] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:43:16 RUNNING pid=18880 hb_age_s=3 stage=a_neg:L9 :: [03:42:02] a_neg 14/16 | [03:42:02] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:45:16 RUNNING pid=18880 hb_age_s=6 stage=a_neg:L24 :: [03:42:02] a_neg 14/16 | [03:42:02] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:47:16 RUNNING pid=18880 hb_age_s=2 stage=a_neg:L6 :: [03:46:27] a_neg 15/16 | [03:46:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:49:17 RUNNING pid=18880 hb_age_s=6 stage=a_neg:L21 :: [03:46:27] a_neg 15/16 | [03:46:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:51:17 RUNNING pid=18880 hb_age_s=1 stage=a_neu:L3 :: [03:50:52] a_neu 0/16 | [03:50:52] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:53:17 RUNNING pid=18880 hb_age_s=5 stage=a_neu:L18 :: [03:50:52] a_neu 0/16 | [03:50:52] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:55:17 RUNNING pid=18880 hb_age_s=0 stage=a_neu:L0 :: [03:55:17] a_neu 1/16 | [03:55:17] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:57:17 RUNNING pid=18880 hb_age_s=4 stage=a_neu:L15 :: [03:55:17] a_neu 1/16 | [03:55:17] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 03:59:18 RUNNING pid=18880 hb_age_s=3 stage=a_neu:L31 :: [03:55:17] a_neu 1/16 | [03:55:17] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:01:18 RUNNING pid=18880 hb_age_s=2 stage=a_neu:L13 :: [03:59:37] a_neu 2/16 | [03:59:37] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:03:18 RUNNING pid=18880 hb_age_s=1 stage=a_neu:L29 :: [03:59:37] a_neu 2/16 | [03:59:37] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:05:18 RUNNING pid=18880 hb_age_s=1 stage=a_neu:L11 :: [04:03:54] a_neu 3/16 | [04:03:54] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:07:19 RUNNING pid=18880 hb_age_s=1 stage=a_neu:L27 :: [04:03:54] a_neu 3/16 | [04:03:54] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:09:19 RUNNING pid=18880 hb_age_s=0 stage=a_neu:L9 :: [04:08:11] a_neu 4/16 | [04:08:11] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:11:19 RUNNING pid=18880 hb_age_s=7 stage=a_neu:L24 :: [04:08:11] a_neu 4/16 | [04:08:11] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:13:19 RUNNING pid=18880 hb_age_s=6 stage=a_neu:L6 :: [04:12:27] a_neu 5/16 | [04:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:15:19 RUNNING pid=18880 hb_age_s=5 stage=a_neu:L22 :: [04:12:27] a_neu 5/16 | [04:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:17:20 RUNNING pid=18880 hb_age_s=5 stage=a_neu:L4 :: [04:16:44] a_neu 6/16 | [04:16:44] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:19:20 RUNNING pid=18880 hb_age_s=4 stage=a_neu:L20 :: [04:16:44] a_neu 6/16 | [04:16:44] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:21:20 RUNNING pid=18880 hb_age_s=2 stage=a_neu:L2 :: [04:21:02] a_neu 7/16 | [04:21:02] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:23:20 RUNNING pid=18880 hb_age_s=1 stage=a_neu:L18 :: [04:21:02] a_neu 7/16 | [04:21:02] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:25:21 RUNNING pid=18880 hb_age_s=1 stage=a_neu:L0 :: [04:25:19] a_neu 8/16 | [04:25:19] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:27:21 RUNNING pid=18880 hb_age_s=6 stage=a_neu:L15 :: [04:25:19] a_neu 8/16 | [04:25:19] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:29:21 RUNNING pid=18880 hb_age_s=4 stage=a_neu:L31 :: [04:25:19] a_neu 8/16 | [04:25:19] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:31:21 RUNNING pid=18880 hb_age_s=1 stage=a_neu:L13 :: [04:29:40] a_neu 9/16 | [04:29:40] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:33:22 RUNNING pid=18880 hb_age_s=1 stage=a_neu:L29 :: [04:29:40] a_neu 9/16 | [04:29:40] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:35:22 RUNNING pid=18880 hb_age_s=0 stage=a_neu:L11 :: [04:33:59] a_neu 10/16 | [04:33:59] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:37:22 RUNNING pid=18880 hb_age_s=7 stage=a_neu:L26 :: [04:33:59] a_neu 10/16 | [04:33:59] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:39:22 RUNNING pid=18880 hb_age_s=6 stage=a_neu:L8 :: [04:38:15] a_neu 11/16 | [04:38:15] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:41:23 RUNNING pid=18880 hb_age_s=6 stage=a_neu:L24 :: [04:38:15] a_neu 11/16 | [04:38:15] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:43:23 RUNNING pid=18880 hb_age_s=4 stage=a_neu:L6 :: [04:42:33] a_neu 12/16 | [04:42:33] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:45:23 RUNNING pid=18880 hb_age_s=4 stage=a_neu:L22 :: [04:42:33] a_neu 12/16 | [04:42:33] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:47:23 RUNNING pid=18880 hb_age_s=3 stage=a_neu:L4 :: [04:46:49] a_neu 13/16 | [04:46:49] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:49:23 RUNNING pid=18880 hb_age_s=2 stage=a_neu:L20 :: [04:46:49] a_neu 13/16 | [04:46:49] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:51:24 RUNNING pid=18880 hb_age_s=2 stage=a_neu:L2 :: [04:51:06] a_neu 14/16 | [04:51:06] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:53:24 RUNNING pid=18880 hb_age_s=2 stage=a_neu:L18 :: [04:51:06] a_neu 14/16 | [04:51:06] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:55:24 RUNNING pid=18880 hb_age_s=1 stage=a_neu:L0 :: [04:55:22] a_neu 15/16 | [04:55:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:57:24 RUNNING pid=18880 hb_age_s=0 stage=a_neu:L16 :: [04:55:22] a_neu 15/16 | [04:55:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 04:59:24 RUNNING pid=18880 hb_age_s=5 stage=a_neu:L31 :: [04:55:22] a_neu 15/16 | [04:55:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 05:01:25 RUNNING pid=18880 hb_age_s=53 stage=kill_table:neutral:refuse :: [05:00:32] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:00:32] kill_table neutral refusal_rate n=12
- 2026-07-31 05:03:25 RUNNING pid=18880 hb_age_s=4 stage=mean_proj:L5 :: [05:00:32] kill_table neutral refusal_rate n=12 | [05:02:35] proj_a:neutral 0/8
- 2026-07-31 05:05:25 RUNNING pid=18880 hb_age_s=-1 stage=mean_proj:L20 :: [05:00:32] kill_table neutral refusal_rate n=12 | [05:02:35] proj_a:neutral 0/8
- 2026-07-31 05:07:25 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L2 :: [05:07:07] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:07:07] proj_a:neutral 1/8
- 2026-07-31 05:09:26 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L16 :: [05:07:07] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:07:07] proj_a:neutral 1/8
- 2026-07-31 05:11:26 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L27 :: [05:07:07] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:07:07] proj_a:neutral 1/8
- 2026-07-31 05:13:26 RUNNING pid=18880 hb_age_s=17 stage=mean_proj:L8 :: [05:12:10] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:12:10] proj_a:neutral 2/8
- 2026-07-31 05:15:26 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L24 :: [05:12:10] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:12:10] proj_a:neutral 2/8
- 2026-07-31 05:17:27 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L6 :: [05:16:36] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:16:36] proj_a:neutral 3/8
- 2026-07-31 05:19:27 RUNNING pid=18880 hb_age_s=2 stage=mean_proj:L19 :: [05:16:36] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:16:36] proj_a:neutral 3/8
- 2026-07-31 05:21:27 RUNNING pid=18880 hb_age_s=5 stage=mean_proj:L32 :: [05:16:36] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:16:36] proj_a:neutral 3/8
- 2026-07-31 05:23:27 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L14 :: [05:21:36] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:21:36] proj_a:neutral 4/8
- 2026-07-31 05:25:27 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L29 :: [05:21:36] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:21:36] proj_a:neutral 4/8
- 2026-07-31 05:27:28 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L5 :: [05:26:45] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:26:45] proj_a:neutral 5/8
- 2026-07-31 05:29:28 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L19 :: [05:26:45] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:26:45] proj_a:neutral 5/8
- 2026-07-31 05:31:28 RUNNING pid=18880 hb_age_s=4 stage=mean_proj:L32 :: [05:26:45] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:26:45] proj_a:neutral 5/8
- 2026-07-31 05:33:28 RUNNING pid=18880 hb_age_s=4 stage=mean_proj:L11 :: [05:31:38] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:31:38] proj_a:neutral 6/8
- 2026-07-31 05:35:28 RUNNING pid=18880 hb_age_s=2 stage=mean_proj:L25 :: [05:31:38] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:31:38] proj_a:neutral 6/8
- 2026-07-31 05:37:29 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L33 :: [05:31:38] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:31:38] proj_a:neutral 6/8
- 2026-07-31 05:39:29 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L11 :: [05:37:30] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:37:30] proj_a:neutral 7/8
- 2026-07-31 05:41:29 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L24 :: [05:37:30] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:37:30] proj_a:neutral 7/8
- 2026-07-31 05:43:29 RUNNING pid=18880 hb_age_s=10 stage=mean_proj:L32 :: [05:37:30] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:37:30] proj_a:neutral 7/8
- 2026-07-31 05:45:30 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L8 :: [05:44:00] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:44:00] proj_r:neutral 0/8
- 2026-07-31 05:47:30 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L18 :: [05:44:00] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:44:00] proj_r:neutral 0/8
- 2026-07-31 05:49:30 RUNNING pid=18880 hb_age_s=21 stage=mean_proj:L28 :: [05:44:00] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:44:00] proj_r:neutral 0/8
- 2026-07-31 05:51:30 RUNNING pid=18880 hb_age_s=7 stage=mean_proj:L6 :: [05:50:19] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:50:19] proj_r:neutral 1/8
- 2026-07-31 05:53:30 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L17 :: [05:50:19] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:50:19] proj_r:neutral 1/8
- 2026-07-31 05:55:30 RUNNING pid=18880 hb_age_s=2 stage=mean_proj:L33 :: [05:50:19] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:50:19] proj_r:neutral 1/8
- 2026-07-31 05:57:31 RUNNING pid=18880 hb_age_s=0 stage=mean_proj:L12 :: [05:55:35] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:55:35] proj_r:neutral 2/8
- 2026-07-31 05:59:31 RUNNING pid=18880 hb_age_s=14 stage=mean_proj:L24 :: [05:55:35] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [05:55:35] proj_r:neutral 2/8
- 2026-07-31 06:01:31 RUNNING pid=18880 hb_age_s=2 stage=mean_proj:L1 :: [06:01:18] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:01:18] proj_r:neutral 3/8
- 2026-07-31 06:03:31 RUNNING pid=18880 hb_age_s=0 stage=mean_proj:L15 :: [06:01:18] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:01:18] proj_r:neutral 3/8
- 2026-07-31 06:05:32 RUNNING pid=18880 hb_age_s=22 stage=mean_proj:L26 :: [06:01:18] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:01:18] proj_r:neutral 3/8
- 2026-07-31 06:07:32 RUNNING pid=18880 hb_age_s=0 stage=mean_proj:L5 :: [06:06:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:06:51] proj_r:neutral 4/8
- 2026-07-31 06:09:32 RUNNING pid=18880 hb_age_s=12 stage=mean_proj:L20 :: [06:06:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:06:51] proj_r:neutral 4/8
- 2026-07-31 06:11:32 RUNNING pid=18880 hb_age_s=4 stage=mean_proj:L32 :: [06:06:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:06:51] proj_r:neutral 4/8
- 2026-07-31 06:13:33 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L11 :: [06:12:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:12:03] proj_r:neutral 5/8
- 2026-07-31 06:15:33 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L25 :: [06:12:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:12:03] proj_r:neutral 5/8
- 2026-07-31 06:17:33 RUNNING pid=18880 hb_age_s=8 stage=mean_proj:L0 :: [06:17:25] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:17:25] proj_r:neutral 6/8
- 2026-07-31 06:19:33 RUNNING pid=18880 hb_age_s=4 stage=mean_proj:L11 :: [06:17:25] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:17:25] proj_r:neutral 6/8
- 2026-07-31 06:21:33 RUNNING pid=18880 hb_age_s=5 stage=mean_proj:L27 :: [06:17:25] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:17:25] proj_r:neutral 6/8
- 2026-07-31 06:23:34 RUNNING pid=18880 hb_age_s=7 stage=mean_proj:L2 :: [06:23:10] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:23:10] proj_r:neutral 7/8
- 2026-07-31 06:25:34 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L14 :: [06:23:10] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:23:10] proj_r:neutral 7/8
- 2026-07-31 06:27:34 RUNNING pid=18880 hb_age_s=0 stage=mean_proj:L25 :: [06:23:10] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:23:10] proj_r:neutral 7/8
- 2026-07-31 06:29:34 RUNNING pid=18880 hb_age_s=13 stage=kill_table:negative:refuse :: [06:29:20] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:29:20] kill_table negative refusal_rate n=12
- 2026-07-31 06:31:34 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L7 :: [06:29:20] kill_table negative refusal_rate n=12 | [06:30:42] proj_a:negative 0/8
- 2026-07-31 06:33:35 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L24 :: [06:29:20] kill_table negative refusal_rate n=12 | [06:30:42] proj_a:negative 0/8
- 2026-07-31 06:35:35 RUNNING pid=18880 hb_age_s=0 stage=mean_proj:L5 :: [06:34:58] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:34:58] proj_a:negative 1/8
- 2026-07-31 06:37:35 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L20 :: [06:34:58] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:34:58] proj_a:negative 1/8
- 2026-07-31 06:39:35 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L2 :: [06:39:15] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:39:15] proj_a:negative 2/8
- 2026-07-31 06:41:36 RUNNING pid=18880 hb_age_s=5 stage=mean_proj:L16 :: [06:39:15] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:39:15] proj_a:negative 2/8
- 2026-07-31 06:43:36 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L31 :: [06:39:15] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:39:15] proj_a:negative 2/8
- 2026-07-31 06:45:36 RUNNING pid=18880 hb_age_s=8 stage=mean_proj:L10 :: [06:44:07] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:44:07] proj_a:negative 3/8
- 2026-07-31 06:47:36 RUNNING pid=18880 hb_age_s=0 stage=mean_proj:L26 :: [06:44:07] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:44:07] proj_a:negative 3/8
- 2026-07-31 06:49:36 RUNNING pid=18880 hb_age_s=4 stage=mean_proj:L5 :: [06:48:52] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:48:52] proj_a:negative 4/8
- 2026-07-31 06:51:37 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L20 :: [06:48:52] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:48:52] proj_a:negative 4/8
- 2026-07-31 06:53:37 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L0 :: [06:53:35] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:53:35] proj_a:negative 5/8
- 2026-07-31 06:55:37 RUNNING pid=18880 hb_age_s=0 stage=mean_proj:L14 :: [06:53:35] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:53:35] proj_a:negative 5/8
- 2026-07-31 06:57:37 RUNNING pid=18880 hb_age_s=5 stage=mean_proj:L27 :: [06:53:35] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:53:35] proj_a:negative 5/8
- 2026-07-31 06:59:37 RUNNING pid=18880 hb_age_s=7 stage=mean_proj:L8 :: [06:58:25] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:58:25] proj_a:negative 6/8
- 2026-07-31 07:01:38 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L24 :: [06:58:25] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [06:58:25] proj_a:negative 6/8
- 2026-07-31 07:03:38 RUNNING pid=18880 hb_age_s=4 stage=mean_proj:L5 :: [07:02:52] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:02:52] proj_a:negative 7/8
- 2026-07-31 07:05:38 RUNNING pid=18880 hb_age_s=2 stage=mean_proj:L21 :: [07:02:52] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:02:52] proj_a:negative 7/8
- 2026-07-31 07:07:38 RUNNING pid=18880 hb_age_s=0 stage=mean_proj:L2 :: [07:07:20] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:07:20] proj_r:negative 0/8
- 2026-07-31 07:09:39 RUNNING pid=18880 hb_age_s=2 stage=mean_proj:L17 :: [07:07:20] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:07:20] proj_r:negative 0/8
- 2026-07-31 07:11:39 RUNNING pid=18880 hb_age_s=5 stage=mean_proj:L31 :: [07:07:20] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:07:20] proj_r:negative 0/8
- 2026-07-31 07:13:39 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L12 :: [07:12:02] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:12:02] proj_r:negative 1/8
- 2026-07-31 07:15:39 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L28 :: [07:12:02] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:12:02] proj_r:negative 1/8
- 2026-07-31 07:17:39 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L8 :: [07:16:35] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:16:35] proj_r:negative 2/8
- 2026-07-31 07:19:40 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L23 :: [07:16:35] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:16:35] proj_r:negative 2/8
- 2026-07-31 07:21:40 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L1 :: [07:21:29] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:21:29] proj_r:negative 3/8
- 2026-07-31 07:23:40 RUNNING pid=18880 hb_age_s=0 stage=mean_proj:L17 :: [07:21:29] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:21:29] proj_r:negative 3/8
- 2026-07-31 07:25:40 RUNNING pid=18880 hb_age_s=0 stage=mean_proj:L31 :: [07:21:29] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:21:29] proj_r:negative 3/8
- 2026-07-31 07:27:40 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L11 :: [07:26:02] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:26:02] proj_r:negative 4/8
- 2026-07-31 07:29:41 RUNNING pid=18880 hb_age_s=7 stage=mean_proj:L25 :: [07:26:02] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:26:02] proj_r:negative 4/8
- 2026-07-31 07:31:41 RUNNING pid=18880 hb_age_s=4 stage=mean_proj:L7 :: [07:30:42] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:30:42] proj_r:negative 5/8
- 2026-07-31 07:33:41 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L23 :: [07:30:42] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:30:42] proj_r:negative 5/8
- 2026-07-31 07:35:41 RUNNING pid=18880 hb_age_s=5 stage=mean_proj:L4 :: [07:35:02] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:35:02] proj_r:negative 6/8
- 2026-07-31 07:37:41 RUNNING pid=18880 hb_age_s=2 stage=mean_proj:L20 :: [07:35:02] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:35:02] proj_r:negative 6/8
- 2026-07-31 07:39:42 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L0 :: [07:39:40] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:39:40] proj_r:negative 7/8
- 2026-07-31 07:41:42 RUNNING pid=18880 hb_age_s=11 stage=mean_proj:L13 :: [07:39:40] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:39:40] proj_r:negative 7/8
- 2026-07-31 07:43:42 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L26 :: [07:39:40] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:39:40] proj_r:negative 7/8
- 2026-07-31 07:45:42 RUNNING pid=18880 hb_age_s=47 stage=kill_table:positive:refuse :: [07:44:55] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:44:55] kill_table positive refusal_rate n=12
- 2026-07-31 07:47:42 RUNNING pid=18880 hb_age_s=0 stage=mean_proj:L5 :: [07:44:55] kill_table positive refusal_rate n=12 | [07:46:48] proj_a:positive 0/8
- 2026-07-31 07:49:43 RUNNING pid=18880 hb_age_s=0 stage=mean_proj:L18 :: [07:44:55] kill_table positive refusal_rate n=12 | [07:46:48] proj_a:positive 0/8
- 2026-07-31 07:51:43 RUNNING pid=18880 hb_age_s=5 stage=mean_proj:L32 :: [07:44:55] kill_table positive refusal_rate n=12 | [07:46:48] proj_a:positive 0/8
- 2026-07-31 07:53:43 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L12 :: [07:51:54] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:51:54] proj_a:positive 1/8
- 2026-07-31 07:55:43 RUNNING pid=18880 hb_age_s=0 stage=mean_proj:L26 :: [07:51:54] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:51:54] proj_a:positive 1/8
- 2026-07-31 07:57:43 RUNNING pid=18880 hb_age_s=5 stage=mean_proj:L5 :: [07:56:57] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:56:57] proj_a:positive 2/8
- 2026-07-31 07:59:44 RUNNING pid=18880 hb_age_s=7 stage=mean_proj:L18 :: [07:56:57] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:56:57] proj_a:positive 2/8
- 2026-07-31 08:01:44 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L32 :: [07:56:57] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:56:57] proj_a:positive 2/8
- 2026-07-31 08:03:44 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L13 :: [08:01:57] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:01:57] proj_a:positive 3/8
- 2026-07-31 08:05:45 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L28 :: [08:01:57] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:01:57] proj_a:positive 3/8
- 2026-07-31 08:07:45 RUNNING pid=18880 hb_age_s=2 stage=mean_proj:L9 :: [08:06:29] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:06:29] proj_a:positive 4/8
- 2026-07-31 08:09:45 RUNNING pid=18880 hb_age_s=5 stage=mean_proj:L23 :: [08:06:29] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:06:29] proj_a:positive 4/8
- 2026-07-31 08:11:46 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L3 :: [08:11:19] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:11:19] proj_a:positive 5/8
- 2026-07-31 08:13:46 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L18 :: [08:11:19] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:11:19] proj_a:positive 5/8
- 2026-07-31 08:15:46 RUNNING pid=18880 hb_age_s=4 stage=mean_proj:L31 :: [08:11:19] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:11:19] proj_a:positive 5/8
- 2026-07-31 08:17:47 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L12 :: [08:16:06] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:16:06] proj_a:positive 6/8
- 2026-07-31 08:19:47 RUNNING pid=18880 hb_age_s=13 stage=mean_proj:L24 :: [08:16:06] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:16:06] proj_a:positive 6/8
- 2026-07-31 08:21:47 RUNNING pid=18880 hb_age_s=8 stage=mean_proj:L3 :: [08:21:10] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:21:10] proj_a:positive 7/8
- 2026-07-31 08:23:47 RUNNING pid=18880 hb_age_s=5 stage=mean_proj:L17 :: [08:21:10] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:21:10] proj_a:positive 7/8
- 2026-07-31 08:25:48 RUNNING pid=18880 hb_age_s=4 stage=mean_proj:L31 :: [08:21:10] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:21:10] proj_a:positive 7/8
- 2026-07-31 08:27:48 RUNNING pid=18880 hb_age_s=2 stage=mean_proj:L11 :: [08:26:10] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:26:10] proj_r:positive 0/8
- 2026-07-31 08:29:48 RUNNING pid=18880 hb_age_s=2 stage=mean_proj:L25 :: [08:26:10] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:26:10] proj_r:positive 0/8
- 2026-07-31 08:31:49 RUNNING pid=18880 hb_age_s=5 stage=mean_proj:L5 :: [08:31:02] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:31:02] proj_r:positive 1/8
- 2026-07-31 08:33:49 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L20 :: [08:31:02] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:31:02] proj_r:positive 1/8
- 2026-07-31 08:35:49 RUNNING pid=18880 hb_age_s=0 stage=mean_proj:L0 :: [08:35:48] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:35:48] proj_r:positive 2/8
- 2026-07-31 08:37:49 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L14 :: [08:35:48] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:35:48] proj_r:positive 2/8
- 2026-07-31 08:39:50 RUNNING pid=18880 hb_age_s=7 stage=mean_proj:L26 :: [08:35:48] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:35:48] proj_r:positive 2/8
- 2026-07-31 08:41:50 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L5 :: [08:41:01] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:41:01] proj_r:positive 3/8
- 2026-07-31 08:43:50 RUNNING pid=18880 hb_age_s=5 stage=mean_proj:L19 :: [08:41:01] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:41:01] proj_r:positive 3/8
- 2026-07-31 08:45:51 RUNNING pid=18880 hb_age_s=2 stage=mean_proj:L30 :: [08:41:01] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:41:01] proj_r:positive 3/8
- 2026-07-31 08:47:51 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L4 :: [08:46:45] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:46:45] proj_r:positive 4/8
- 2026-07-31 08:49:51 RUNNING pid=18880 hb_age_s=13 stage=mean_proj:L12 :: [08:46:45] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:46:45] proj_r:positive 4/8
- 2026-07-31 08:51:52 RUNNING pid=18880 hb_age_s=16 stage=mean_proj:L20 :: [08:46:45] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [08:46:45] proj_r:positive 4/8
- 2026-07-31 12:34:04 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L4 :: [12:32:36] proj_r:positive skip 4: mean_proj: avg layer time >120s at L20 | [12:32:36] proj_r:positive 5/8
- 2026-07-31 12:36:04 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L10 :: [12:32:36] proj_r:positive skip 4: mean_proj: avg layer time >120s at L20 | [12:32:36] proj_r:positive 5/8
- 2026-07-31 12:38:05 RUNNING pid=18880 hb_age_s=8 stage=mean_proj:L17 :: [12:32:36] proj_r:positive skip 4: mean_proj: avg layer time >120s at L20 | [12:32:36] proj_r:positive 5/8
- 2026-07-31 12:40:05 RUNNING pid=18880 hb_age_s=5 stage=mean_proj:L26 :: [12:32:36] proj_r:positive skip 4: mean_proj: avg layer time >120s at L20 | [12:32:36] proj_r:positive 5/8
- 2026-07-31 12:42:05 RUNNING pid=18880 hb_age_s=1 stage=mean_proj:L5 :: [12:41:18] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [12:41:18] proj_r:positive 6/8
- 2026-07-31 12:44:06 RUNNING pid=18880 hb_age_s=2 stage=mean_proj:L20 :: [12:41:18] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [12:41:18] proj_r:positive 6/8
- 2026-07-31 12:46:06 RUNNING pid=18880 hb_age_s=6 stage=mean_proj:L32 :: [12:41:18] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [12:41:18] proj_r:positive 6/8
- 2026-07-31 12:48:06 RUNNING pid=18880 hb_age_s=7 stage=mean_proj:L13 :: [12:46:15] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [12:46:15] proj_r:positive 7/8
- 2026-07-31 12:50:06 RUNNING pid=18880 hb_age_s=3 stage=mean_proj:L27 :: [12:46:15] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [12:46:15] proj_r:positive 7/8
- 2026-07-31 12:52:06 RUNNING pid=18880 hb_age_s=22 stage=h_img:L4 :: [12:50:57] h_img 0/16 | [12:50:57] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 12:54:07 RUNNING pid=18880 hb_age_s=6 stage=h_img:L17 :: [12:50:57] h_img 0/16 | [12:50:57] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 12:56:07 RUNNING pid=18880 hb_age_s=13 stage=h_img:L26 :: [12:50:57] h_img 0/16 | [12:50:57] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 12:58:07 RUNNING pid=18880 hb_age_s=2 stage=h_img:L32 :: [12:50:57] h_img 0/16 | [12:50:57] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:00:07 RUNNING pid=18880 hb_age_s=0 stage=h_img:L9 :: [12:58:43] h_img 1/16 | [12:58:43] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:02:08 RUNNING pid=18880 hb_age_s=2 stage=h_img:L22 :: [12:58:43] h_img 1/16 | [12:58:43] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:04:08 RUNNING pid=18880 hb_age_s=6 stage=h_img:L33 :: [12:58:43] h_img 1/16 | [12:58:43] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:06:08 RUNNING pid=18880 hb_age_s=29 stage=h_img:L13 :: [13:04:08] h_img 2/16 | [13:04:08] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:08:08 RUNNING pid=18880 hb_age_s=28 stage=h_img:L26 :: [13:04:08] h_img 2/16 | [13:04:08] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:10:08 RUNNING pid=18880 hb_age_s=6 stage=h_img:L8 :: [13:09:00] h_img 3/16 | [13:09:00] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:12:09 RUNNING pid=18880 hb_age_s=26 stage=h_img:L22 :: [13:09:00] h_img 3/16 | [13:09:00] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:14:09 RUNNING pid=18880 hb_age_s=11 stage=h_img:L0 :: [13:13:58] h_img 4/16 | [13:13:58] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:16:09 RUNNING pid=18880 hb_age_s=15 stage=h_img:L7 :: [13:13:58] h_img 4/16 | [13:13:58] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:18:09 RUNNING pid=18880 hb_age_s=11 stage=h_img:L15 :: [13:13:58] h_img 4/16 | [13:13:58] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:20:10 RUNNING pid=18880 hb_age_s=4 stage=h_img:L21 :: [13:13:58] h_img 4/16 | [13:13:58] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:22:10 RUNNING pid=18880 hb_age_s=27 stage=h_img:L24 :: [13:13:58] h_img 4/16 | [13:13:58] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:24:10 RUNNING pid=18880 hb_age_s=4 stage=h_img:L5 :: [13:23:26] h_img 5/16 | [13:23:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:26:10 RUNNING pid=18880 hb_age_s=2 stage=h_img:L16 :: [13:23:26] h_img 5/16 | [13:23:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:28:11 RUNNING pid=18880 hb_age_s=4 stage=h_img:L25 :: [13:23:26] h_img 5/16 | [13:23:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:30:11 RUNNING pid=18880 hb_age_s=6 stage=h_img:L6 :: [13:29:20] h_img 6/16 | [13:29:20] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:32:11 RUNNING pid=18880 hb_age_s=25 stage=h_img:L13 :: [13:29:20] h_img 6/16 | [13:29:20] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:34:11 RUNNING pid=18880 hb_age_s=4 stage=h_img:L23 :: [13:29:20] h_img 6/16 | [13:29:20] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:36:12 RUNNING pid=18880 hb_age_s=7 stage=h_img:L4 :: [13:35:31] h_img 7/16 | [13:35:31] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:38:12 RUNNING pid=18880 hb_age_s=7 stage=h_img:L17 :: [13:35:31] h_img 7/16 | [13:35:31] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:40:12 RUNNING pid=18880 hb_age_s=5 stage=h_img:L28 :: [13:35:31] h_img 7/16 | [13:35:31] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:42:12 RUNNING pid=18880 hb_age_s=3 stage=h_img:L8 :: [13:40:51] h_img 8/16 | [13:40:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:44:12 RUNNING pid=18880 hb_age_s=5 stage=h_img:L24 :: [13:40:51] h_img 8/16 | [13:40:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:46:13 RUNNING pid=18880 hb_age_s=0 stage=h_img:L7 :: [13:45:21] h_img 9/16 | [13:45:21] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:48:13 RUNNING pid=18880 hb_age_s=0 stage=h_img:L18 :: [13:45:21] h_img 9/16 | [13:45:21] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:50:13 RUNNING pid=18880 hb_age_s=4 stage=h_img:L0 :: [13:50:09] h_img 10/16 | [13:50:09] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:52:14 RUNNING pid=18880 hb_age_s=5 stage=h_img:L17 :: [13:50:09] h_img 10/16 | [13:50:09] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:54:14 RUNNING pid=18880 hb_age_s=25 stage=h_img:L28 :: [13:50:09] h_img 10/16 | [13:50:09] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:56:14 RUNNING pid=18880 hb_age_s=11 stage=h_img:L6 :: [13:54:54] h_img 11/16 | [13:54:54] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 13:58:14 RUNNING pid=18880 hb_age_s=5 stage=h_img:L14 :: [13:54:54] h_img 11/16 | [13:54:54] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 14:00:14 RUNNING pid=18880 hb_age_s=0 stage=h_img:L28 :: [13:54:54] h_img 11/16 | [13:54:54] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 14:02:15 RUNNING pid=18880 hb_age_s=13 stage=h_img:L6 :: [14:00:59] h_img 12/16 | [14:00:59] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 14:04:15 RUNNING pid=18880 hb_age_s=6 stage=h_img:L18 :: [14:00:59] h_img 12/16 | [14:00:59] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 14:06:15 RUNNING pid=18880 hb_age_s=3 stage=h_img:L33 :: [14:00:59] h_img 12/16 | [14:00:59] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 14:08:15 RUNNING pid=18880 hb_age_s=3 stage=h_img:L13 :: [14:06:18] h_img 13/16 | [14:06:18] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 14:10:16 RUNNING pid=18880 hb_age_s=1 stage=h_img:L28 :: [14:06:18] h_img 13/16 | [14:06:18] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 14:12:16 RUNNING pid=18880 hb_age_s=3 stage=h_img:L11 :: [14:10:57] h_img 14/16 | [14:10:57] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 14:14:16 RUNNING pid=18880 hb_age_s=1 stage=h_img:L28 :: [14:10:57] h_img 14/16 | [14:10:57] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 14:16:16 RUNNING pid=18880 hb_age_s=23 stage=h_img:L7 :: [14:15:00] h_img 15/16 | [14:15:00] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 14:18:16 RUNNING pid=18880 hb_age_s=4 stage=h_img:L22 :: [14:15:00] h_img 15/16 | [14:15:00] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 14:20:17 RUNNING pid=18880 hb_age_s=33 stage=h_img:L28 :: [14:15:00] h_img 15/16 | [14:15:00] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 14:22:17 RUNNING pid=18880 hb_age_s=5 stage=delta_img_a:L0 :: [14:15:00] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [14:22:12] delta_img_a 0/16
- 2026-07-31 14:24:17 RUNNING pid=18880 hb_age_s=3 stage=delta_img_a:L17 :: [14:15:00] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [14:22:12] delta_img_a 0/16
- 2026-07-31 14:26:17 RUNNING pid=18880 hb_age_s=1 stage=delta_img_a:L28 :: [14:15:00] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [14:22:12] delta_img_a 0/16
- 2026-07-31 14:28:18 RUNNING pid=18880 hb_age_s=24 stage=delta_img_a:L4 :: [14:22:12] delta_img_a 0/16 | [14:26:59] delta_img_a 1/16
- 2026-07-31 14:30:18 RUNNING pid=18880 hb_age_s=3 stage=delta_img_a:L17 :: [14:22:12] delta_img_a 0/16 | [14:26:59] delta_img_a 1/16
- 2026-07-31 14:32:18 RUNNING pid=18880 hb_age_s=26 stage=delta_img_a:L27 :: [14:22:12] delta_img_a 0/16 | [14:26:59] delta_img_a 1/16
- 2026-07-31 14:34:18 RUNNING pid=18880 hb_age_s=26 stage=delta_img_a:L3 :: [14:26:59] delta_img_a 1/16 | [14:33:11] delta_img_a 2/16
- 2026-07-31 14:36:18 RUNNING pid=18880 hb_age_s=20 stage=delta_img_a:L14 :: [14:26:59] delta_img_a 1/16 | [14:33:11] delta_img_a 2/16
- 2026-07-31 14:38:19 RUNNING pid=18880 hb_age_s=9 stage=delta_img_a:L23 :: [14:26:59] delta_img_a 1/16 | [14:33:11] delta_img_a 2/16
- 2026-07-31 14:40:19 RUNNING pid=18880 hb_age_s=3 stage=delta_img_a:L30 :: [14:26:59] delta_img_a 1/16 | [14:33:11] delta_img_a 2/16
- 2026-07-31 14:42:19 RUNNING pid=18880 hb_age_s=5 stage=delta_img_a:L11 :: [14:33:11] delta_img_a 2/16 | [14:40:49] delta_img_a 3/16
- 2026-07-31 14:44:19 RUNNING pid=18880 hb_age_s=17 stage=delta_img_a:L23 :: [14:33:11] delta_img_a 2/16 | [14:40:49] delta_img_a 3/16
- 2026-07-31 14:46:19 RUNNING pid=18880 hb_age_s=-1 stage=delta_img_a:L2 :: [14:40:49] delta_img_a 3/16 | [14:46:04] delta_img_a 4/16
- 2026-07-31 14:48:20 RUNNING pid=18880 hb_age_s=6 stage=delta_img_a:L17 :: [14:40:49] delta_img_a 3/16 | [14:46:04] delta_img_a 4/16
- 2026-07-31 14:50:20 RUNNING pid=18880 hb_age_s=6 stage=delta_img_a:L32 :: [14:40:49] delta_img_a 3/16 | [14:46:04] delta_img_a 4/16
- 2026-07-31 14:52:20 RUNNING pid=18880 hb_age_s=20 stage=delta_img_a:L11 :: [14:46:04] delta_img_a 4/16 | [14:50:30] delta_img_a 5/16
- 2026-07-31 14:54:20 RUNNING pid=18880 hb_age_s=1 stage=delta_img_a:L26 :: [14:46:04] delta_img_a 4/16 | [14:50:30] delta_img_a 5/16
- 2026-07-31 14:56:21 RUNNING pid=18880 hb_age_s=3 stage=delta_img_a:L8 :: [14:50:30] delta_img_a 5/16 | [14:55:17] delta_img_a 6/16
- 2026-07-31 14:58:21 RUNNING pid=18880 hb_age_s=2 stage=delta_img_a:L19 :: [14:50:30] delta_img_a 5/16 | [14:55:17] delta_img_a 6/16
- 2026-07-31 15:00:21 RUNNING pid=18880 hb_age_s=9 stage=delta_img_a:L31 :: [14:50:30] delta_img_a 5/16 | [14:55:17] delta_img_a 6/16
- 2026-07-31 15:02:21 RUNNING pid=18880 hb_age_s=6 stage=delta_img_a:L8 :: [14:55:17] delta_img_a 6/16 | [15:01:14] delta_img_a 7/16
- 2026-07-31 15:04:21 RUNNING pid=18880 hb_age_s=0 stage=delta_img_a:L24 :: [14:55:17] delta_img_a 6/16 | [15:01:14] delta_img_a 7/16
- 2026-07-31 15:06:22 RUNNING pid=18880 hb_age_s=6 stage=delta_img_a:L3 :: [15:01:14] delta_img_a 7/16 | [15:05:54] delta_img_a 8/16
- 2026-07-31 15:08:22 RUNNING pid=18880 hb_age_s=1 stage=delta_img_a:L17 :: [15:01:14] delta_img_a 7/16 | [15:05:54] delta_img_a 8/16
- 2026-07-31 15:10:22 RUNNING pid=18880 hb_age_s=5 stage=delta_img_a:L29 :: [15:01:14] delta_img_a 7/16 | [15:05:54] delta_img_a 8/16
- 2026-07-31 15:12:22 RUNNING pid=18880 hb_age_s=4 stage=delta_img_a:L4 :: [15:05:54] delta_img_a 8/16 | [15:11:21] delta_img_a 9/16
- 2026-07-31 15:14:22 RUNNING pid=18880 hb_age_s=5 stage=delta_img_a:L20 :: [15:05:54] delta_img_a 8/16 | [15:11:21] delta_img_a 9/16
- 2026-07-31 15:16:23 RUNNING pid=18880 hb_age_s=5 stage=delta_img_a:L30 :: [15:05:54] delta_img_a 8/16 | [15:11:21] delta_img_a 9/16
- 2026-07-31 15:18:23 RUNNING pid=18880 hb_age_s=1 stage=delta_img_a:L12 :: [15:11:21] delta_img_a 9/16 | [15:16:48] delta_img_a 10/16
- 2026-07-31 15:20:23 RUNNING pid=18880 hb_age_s=4 stage=delta_img_a:L26 :: [15:11:21] delta_img_a 9/16 | [15:16:48] delta_img_a 10/16
- 2026-07-31 15:22:23 RUNNING pid=18880 hb_age_s=2 stage=delta_img_a:L6 :: [15:16:48] delta_img_a 10/16 | [15:21:36] delta_img_a 11/16
- 2026-07-31 15:24:24 RUNNING pid=18880 hb_age_s=5 stage=delta_img_a:L20 :: [15:16:48] delta_img_a 10/16 | [15:21:36] delta_img_a 11/16
- 2026-07-31 15:26:24 RUNNING pid=18880 hb_age_s=24 stage=delta_img_a:L0 :: [15:21:36] delta_img_a 11/16 | [15:26:00] delta_img_a 12/16
- 2026-07-31 15:28:24 RUNNING pid=18880 hb_age_s=1 stage=delta_img_a:L17 :: [15:21:36] delta_img_a 11/16 | [15:26:00] delta_img_a 12/16
- 2026-07-31 15:30:24 RUNNING pid=18880 hb_age_s=1 stage=delta_img_a:L31 :: [15:21:36] delta_img_a 11/16 | [15:26:00] delta_img_a 12/16
- 2026-07-31 15:32:25 RUNNING pid=18880 hb_age_s=3 stage=delta_img_a:L14 :: [15:26:00] delta_img_a 12/16 | [15:30:44] delta_img_a 13/16
- 2026-07-31 15:34:25 RUNNING pid=18880 hb_age_s=1 stage=delta_img_a:L31 :: [15:26:00] delta_img_a 12/16 | [15:30:44] delta_img_a 13/16
- 2026-07-31 15:36:25 RUNNING pid=18880 hb_age_s=6 stage=delta_img_a:L12 :: [15:30:44] delta_img_a 13/16 | [15:34:44] delta_img_a 14/16
- 2026-07-31 15:38:25 RUNNING pid=18880 hb_age_s=5 stage=delta_img_a:L26 :: [15:30:44] delta_img_a 13/16 | [15:34:44] delta_img_a 14/16
- 2026-07-31 15:40:26 RUNNING pid=18880 hb_age_s=7 stage=delta_img_a:L5 :: [15:34:44] delta_img_a 14/16 | [15:39:19] delta_img_a 15/16
- 2026-07-31 15:42:26 RUNNING pid=18880 hb_age_s=12 stage=delta_img_a:L17 :: [15:34:44] delta_img_a 14/16 | [15:39:19] delta_img_a 15/16
- 2026-07-31 15:44:26 RUNNING pid=18880 hb_age_s=4 stage=delta_img_a:L32 :: [15:34:44] delta_img_a 14/16 | [15:39:19] delta_img_a 15/16
- 2026-07-31 15:46:26 RUNNING pid=18880 hb_age_s=3 stage=neu_img_a:L12 :: [15:39:19] delta_img_a 15/16 | [15:44:39] neu_img_a 0/16
- 2026-07-31 15:48:26 RUNNING pid=18880 hb_age_s=3 stage=neu_img_a:L26 :: [15:39:19] delta_img_a 15/16 | [15:44:39] neu_img_a 0/16
- 2026-07-31 15:50:27 RUNNING pid=18880 hb_age_s=5 stage=neu_img_a:L6 :: [15:44:39] neu_img_a 0/16 | [15:49:19] neu_img_a 1/16
- 2026-07-31 15:52:27 RUNNING pid=18880 hb_age_s=3 stage=neu_img_a:L20 :: [15:44:39] neu_img_a 0/16 | [15:49:19] neu_img_a 1/16
- 2026-07-31 15:54:27 RUNNING pid=18880 hb_age_s=6 stage=neu_img_a:L2 :: [15:49:19] neu_img_a 1/16 | [15:54:07] neu_img_a 2/16
- 2026-07-31 15:56:27 RUNNING pid=18880 hb_age_s=8 stage=neu_img_a:L17 :: [15:49:19] neu_img_a 1/16 | [15:54:07] neu_img_a 2/16
- 2026-07-31 15:58:27 RUNNING pid=18880 hb_age_s=14 stage=neu_img_a:L32 :: [15:49:19] neu_img_a 1/16 | [15:54:07] neu_img_a 2/16
- 2026-07-31 16:00:28 RUNNING pid=18880 hb_age_s=20 stage=neu_img_a:L10 :: [15:54:07] neu_img_a 2/16 | [15:58:47] neu_img_a 3/16
- 2026-07-31 16:02:28 RUNNING pid=18880 hb_age_s=0 stage=neu_img_a:L18 :: [15:54:07] neu_img_a 2/16 | [15:58:47] neu_img_a 3/16
- 2026-07-31 16:04:28 RUNNING pid=18880 hb_age_s=3 stage=neu_img_a:L0 :: [15:58:47] neu_img_a 3/16 | [16:04:25] neu_img_a 4/16
- 2026-07-31 16:06:28 RUNNING pid=18880 hb_age_s=9 stage=neu_img_a:L16 :: [15:58:47] neu_img_a 3/16 | [16:04:25] neu_img_a 4/16
- 2026-07-31 16:08:29 RUNNING pid=18880 hb_age_s=6 stage=neu_img_a:L27 :: [15:58:47] neu_img_a 3/16 | [16:04:25] neu_img_a 4/16
- 2026-07-31 16:10:29 RUNNING pid=18880 hb_age_s=3 stage=neu_img_a:L7 :: [16:04:25] neu_img_a 4/16 | [16:09:36] neu_img_a 5/16
- 2026-07-31 16:12:29 RUNNING pid=18880 hb_age_s=4 stage=neu_img_a:L23 :: [16:04:25] neu_img_a 4/16 | [16:09:36] neu_img_a 5/16
- 2026-07-31 16:14:29 RUNNING pid=18880 hb_age_s=5 stage=neu_img_a:L6 :: [16:09:36] neu_img_a 5/16 | [16:13:41] neu_img_a 6/16
- 2026-07-31 16:16:29 RUNNING pid=18880 hb_age_s=3 stage=neu_img_a:L18 :: [16:09:36] neu_img_a 5/16 | [16:13:41] neu_img_a 6/16
- 2026-07-31 16:18:30 RUNNING pid=18880 hb_age_s=2 stage=neu_img_a:L1 :: [16:13:41] neu_img_a 6/16 | [16:18:20] neu_img_a 7/16
- 2026-07-31 16:20:30 RUNNING pid=18880 hb_age_s=7 stage=neu_img_a:L13 :: [16:13:41] neu_img_a 6/16 | [16:18:20] neu_img_a 7/16
- 2026-07-31 16:22:30 RUNNING pid=18880 hb_age_s=6 stage=neu_img_a:L24 :: [16:13:41] neu_img_a 6/16 | [16:18:20] neu_img_a 7/16
- 2026-07-31 16:24:30 RUNNING pid=18880 hb_age_s=0 stage=neu_img_a:L5 :: [16:18:20] neu_img_a 7/16 | [16:23:36] neu_img_a 8/16
- 2026-07-31 16:26:30 RUNNING pid=18880 hb_age_s=0 stage=neu_img_a:L22 :: [16:18:20] neu_img_a 7/16 | [16:23:36] neu_img_a 8/16
- 2026-07-31 16:28:31 RUNNING pid=18880 hb_age_s=5 stage=neu_img_a:L1 :: [16:23:36] neu_img_a 8/16 | [16:28:18] neu_img_a 9/16
- 2026-07-31 16:30:31 RUNNING pid=18880 hb_age_s=0 stage=neu_img_a:L16 :: [16:23:36] neu_img_a 8/16 | [16:28:18] neu_img_a 9/16
- 2026-07-31 16:32:32 RUNNING pid=18880 hb_age_s=2 stage=neu_img_a:L30 :: [16:23:36] neu_img_a 8/16 | [16:28:18] neu_img_a 9/16
- 2026-07-31 16:34:32 RUNNING pid=18880 hb_age_s=3 stage=neu_img_a:L10 :: [16:28:18] neu_img_a 9/16 | [16:32:58] neu_img_a 10/16
- 2026-07-31 16:36:32 RUNNING pid=18880 hb_age_s=19 stage=neu_img_a:L20 :: [16:28:18] neu_img_a 9/16 | [16:32:58] neu_img_a 10/16
- 2026-07-31 16:38:32 RUNNING pid=18880 hb_age_s=3 stage=neu_img_a:L33 :: [16:28:18] neu_img_a 9/16 | [16:32:58] neu_img_a 10/16
- 2026-07-31 16:40:32 RUNNING pid=18880 hb_age_s=2 stage=neu_img_a:L15 :: [16:32:58] neu_img_a 10/16 | [16:38:36] neu_img_a 11/16
- 2026-07-31 16:42:33 RUNNING pid=18880 hb_age_s=2 stage=neu_img_a:L26 :: [16:32:58] neu_img_a 10/16 | [16:38:36] neu_img_a 11/16
- 2026-07-31 16:44:33 RUNNING pid=18880 hb_age_s=6 stage=neu_img_a:L5 :: [16:38:36] neu_img_a 11/16 | [16:43:29] neu_img_a 12/16
- 2026-07-31 16:46:33 RUNNING pid=18880 hb_age_s=2 stage=neu_img_a:L16 :: [16:38:36] neu_img_a 11/16 | [16:43:29] neu_img_a 12/16
- 2026-07-31 16:48:33 RUNNING pid=18880 hb_age_s=1 stage=neu_img_a:L30 :: [16:38:36] neu_img_a 11/16 | [16:43:29] neu_img_a 12/16
- 2026-07-31 16:50:34 RUNNING pid=18880 hb_age_s=1 stage=neu_img_a:L13 :: [16:43:29] neu_img_a 12/16 | [16:48:59] neu_img_a 13/16
- 2026-07-31 16:52:34 RUNNING pid=18880 hb_age_s=9 stage=neu_img_a:L25 :: [16:43:29] neu_img_a 12/16 | [16:48:59] neu_img_a 13/16
- 2026-07-31 16:54:34 RUNNING pid=18880 hb_age_s=6 stage=neu_img_a:L2 :: [16:48:59] neu_img_a 13/16 | [16:53:52] neu_img_a 14/16
- 2026-07-31 16:56:34 RUNNING pid=18880 hb_age_s=1 stage=neu_img_a:L16 :: [16:48:59] neu_img_a 13/16 | [16:53:52] neu_img_a 14/16
- 2026-07-31 16:58:34 RUNNING pid=18880 hb_age_s=1 stage=neu_img_a:L32 :: [16:48:59] neu_img_a 13/16 | [16:53:52] neu_img_a 14/16
- 2026-07-31 17:00:35 RUNNING pid=18880 hb_age_s=31 stage=neu_img_a:L10 :: [16:53:52] neu_img_a 14/16 | [16:58:47] neu_img_a 15/16
- 2026-07-31 17:02:35 RUNNING pid=18880 hb_age_s=1 stage=neu_img_a:L23 :: [16:53:52] neu_img_a 14/16 | [16:58:47] neu_img_a 15/16
- 2026-07-31 17:04:35 RUNNING pid=18880 hb_age_s=6 stage=harm_img_h:L4 :: [16:58:47] neu_img_a 15/16 | [17:04:02] harm_img_h 0/16
- 2026-07-31 17:06:35 RUNNING pid=18880 hb_age_s=3 stage=harm_img_h:L21 :: [16:58:47] neu_img_a 15/16 | [17:04:02] harm_img_h 0/16
- 2026-07-31 17:08:36 RUNNING pid=18880 hb_age_s=0 stage=harm_img_h:L4 :: [17:04:02] harm_img_h 0/16 | [17:08:06] harm_img_h 1/16
- 2026-07-31 17:10:36 RUNNING pid=18880 hb_age_s=5 stage=harm_img_h:L20 :: [17:04:02] harm_img_h 0/16 | [17:08:06] harm_img_h 1/16
- 2026-07-31 17:12:36 RUNNING pid=18880 hb_age_s=2 stage=harm_img_h:L3 :: [17:08:06] harm_img_h 1/16 | [17:12:12] harm_img_h 2/16
- 2026-07-31 17:14:36 RUNNING pid=18880 hb_age_s=6 stage=harm_img_h:L19 :: [17:08:06] harm_img_h 1/16 | [17:12:12] harm_img_h 2/16
- 2026-07-31 17:16:37 RUNNING pid=18880 hb_age_s=6 stage=harm_img_h:L1 :: [17:12:12] harm_img_h 2/16 | [17:16:23] harm_img_h 3/16
- 2026-07-31 17:18:37 RUNNING pid=18880 hb_age_s=7 stage=harm_img_h:L17 :: [17:12:12] harm_img_h 2/16 | [17:16:23] harm_img_h 3/16
- 2026-07-31 17:20:37 RUNNING pid=18880 hb_age_s=2 stage=harm_img_h:L33 :: [17:12:12] harm_img_h 2/16 | [17:16:23] harm_img_h 3/16
- 2026-07-31 17:22:37 RUNNING pid=18880 hb_age_s=6 stage=harm_img_h:L14 :: [17:16:23] harm_img_h 3/16 | [17:20:42] harm_img_h 4/16
- 2026-07-31 17:24:37 RUNNING pid=18880 hb_age_s=3 stage=harm_img_h:L30 :: [17:16:23] harm_img_h 3/16 | [17:20:42] harm_img_h 4/16
- 2026-07-31 17:26:38 RUNNING pid=18880 hb_age_s=1 stage=harm_img_h:L12 :: [17:20:42] harm_img_h 4/16 | [17:25:04] harm_img_h 5/16
- 2026-07-31 17:28:38 RUNNING pid=18880 hb_age_s=5 stage=harm_img_h:L27 :: [17:20:42] harm_img_h 4/16 | [17:25:04] harm_img_h 5/16
- 2026-07-31 17:30:38 RUNNING pid=18880 hb_age_s=2 stage=harm_img_h:L9 :: [17:25:04] harm_img_h 5/16 | [17:29:26] harm_img_h 6/16
- 2026-07-31 17:32:38 RUNNING pid=18880 hb_age_s=6 stage=harm_img_h:L24 :: [17:25:04] harm_img_h 5/16 | [17:29:26] harm_img_h 6/16
- 2026-07-31 17:34:39 RUNNING pid=18880 hb_age_s=4 stage=harm_img_h:L6 :: [17:29:26] harm_img_h 6/16 | [17:33:48] harm_img_h 7/16
- 2026-07-31 17:36:39 RUNNING pid=18880 hb_age_s=6 stage=harm_img_h:L21 :: [17:29:26] harm_img_h 6/16 | [17:33:48] harm_img_h 7/16
- 2026-07-31 17:38:39 RUNNING pid=18880 hb_age_s=3 stage=harm_img_h:L3 :: [17:33:48] harm_img_h 7/16 | [17:38:13] harm_img_h 8/16
- 2026-07-31 17:40:39 RUNNING pid=18880 hb_age_s=6 stage=harm_img_h:L18 :: [17:33:48] harm_img_h 7/16 | [17:38:13] harm_img_h 8/16
- 2026-07-31 17:42:39 RUNNING pid=18880 hb_age_s=3 stage=harm_img_h:L0 :: [17:38:13] harm_img_h 8/16 | [17:42:36] harm_img_h 9/16
- 2026-07-31 17:44:40 RUNNING pid=18880 hb_age_s=0 stage=harm_img_h:L16 :: [17:38:13] harm_img_h 8/16 | [17:42:36] harm_img_h 9/16
- 2026-07-31 17:46:40 RUNNING pid=18880 hb_age_s=1 stage=harm_img_h:L31 :: [17:38:13] harm_img_h 8/16 | [17:42:36] harm_img_h 9/16
- 2026-07-31 17:48:40 RUNNING pid=18880 hb_age_s=0 stage=harm_img_h:L11 :: [17:42:36] harm_img_h 9/16 | [17:47:03] harm_img_h 10/16
- 2026-07-31 17:50:40 RUNNING pid=18880 hb_age_s=7 stage=harm_img_h:L24 :: [17:42:36] harm_img_h 9/16 | [17:47:03] harm_img_h 10/16
- 2026-07-31 17:52:41 RUNNING pid=18880 hb_age_s=4 stage=harm_img_h:L5 :: [17:47:03] harm_img_h 10/16 | [17:51:57] harm_img_h 11/16
- 2026-07-31 17:54:41 RUNNING pid=18880 hb_age_s=0 stage=harm_img_h:L21 :: [17:47:03] harm_img_h 10/16 | [17:51:57] harm_img_h 11/16
- 2026-07-31 17:56:41 RUNNING pid=18880 hb_age_s=3 stage=harm_img_h:L2 :: [17:51:57] harm_img_h 11/16 | [17:56:22] harm_img_h 12/16
- 2026-07-31 17:58:41 RUNNING pid=18880 hb_age_s=-1 stage=harm_img_h:L18 :: [17:51:57] harm_img_h 11/16 | [17:56:22] harm_img_h 12/16
- 2026-07-31 18:00:42 RUNNING pid=18880 hb_age_s=6 stage=harm_img_h:L32 :: [17:51:57] harm_img_h 11/16 | [17:56:22] harm_img_h 12/16
- 2026-07-31 18:02:42 RUNNING pid=18880 hb_age_s=1 stage=harm_img_h:L14 :: [17:56:22] harm_img_h 12/16 | [18:00:52] harm_img_h 13/16
- 2026-07-31 18:04:42 RUNNING pid=18880 hb_age_s=4 stage=harm_img_h:L29 :: [17:56:22] harm_img_h 12/16 | [18:00:52] harm_img_h 13/16
- 2026-07-31 18:06:42 RUNNING pid=18880 hb_age_s=0 stage=harm_img_h:L11 :: [18:00:52] harm_img_h 13/16 | [18:05:16] harm_img_h 14/16
- 2026-07-31 18:08:42 RUNNING pid=18880 hb_age_s=3 stage=harm_img_h:L26 :: [18:00:52] harm_img_h 13/16 | [18:05:16] harm_img_h 14/16
- 2026-07-31 18:10:43 RUNNING pid=18880 hb_age_s=0 stage=harm_img_h:L8 :: [18:05:16] harm_img_h 14/16 | [18:09:40] harm_img_h 15/16
- 2026-07-31 18:12:43 RUNNING pid=18880 hb_age_s=4 stage=harm_img_h:L23 :: [18:05:16] harm_img_h 14/16 | [18:09:40] harm_img_h 15/16
- 2026-07-31 18:14:43 RUNNING pid=18880 hb_age_s=4 stage=neu_img_h:L4 :: [18:09:40] harm_img_h 15/16 | [18:14:09] neu_img_h 0/16
- 2026-07-31 18:16:43 RUNNING pid=18880 hb_age_s=6 stage=neu_img_h:L19 :: [18:09:40] harm_img_h 15/16 | [18:14:09] neu_img_h 0/16
- 2026-07-31 18:18:44 RUNNING pid=18880 hb_age_s=3 stage=neu_img_h:L1 :: [18:14:09] neu_img_h 0/16 | [18:18:33] neu_img_h 1/16
- 2026-07-31 18:20:44 RUNNING pid=18880 hb_age_s=6 stage=neu_img_h:L16 :: [18:14:09] neu_img_h 0/16 | [18:18:33] neu_img_h 1/16
- 2026-07-31 18:22:44 RUNNING pid=18880 hb_age_s=2 stage=neu_img_h:L32 :: [18:14:09] neu_img_h 0/16 | [18:18:33] neu_img_h 1/16
- 2026-07-31 18:24:44 RUNNING pid=18880 hb_age_s=6 stage=neu_img_h:L13 :: [18:18:33] neu_img_h 1/16 | [18:22:57] neu_img_h 2/16
- 2026-07-31 18:26:45 RUNNING pid=18880 hb_age_s=1 stage=neu_img_h:L29 :: [18:18:33] neu_img_h 1/16 | [18:22:57] neu_img_h 2/16
- 2026-07-31 18:28:45 RUNNING pid=18880 hb_age_s=6 stage=neu_img_h:L10 :: [18:22:57] neu_img_h 2/16 | [18:27:21] neu_img_h 3/16
- 2026-07-31 18:30:45 RUNNING pid=18880 hb_age_s=2 stage=neu_img_h:L26 :: [18:22:57] neu_img_h 2/16 | [18:27:21] neu_img_h 3/16
- 2026-07-31 18:32:45 RUNNING pid=18880 hb_age_s=6 stage=neu_img_h:L7 :: [18:27:21] neu_img_h 3/16 | [18:31:44] neu_img_h 4/16
- 2026-07-31 18:34:45 RUNNING pid=18880 hb_age_s=2 stage=neu_img_h:L23 :: [18:27:21] neu_img_h 3/16 | [18:31:44] neu_img_h 4/16
- 2026-07-31 18:36:46 RUNNING pid=18880 hb_age_s=4 stage=neu_img_h:L4 :: [18:31:44] neu_img_h 4/16 | [18:36:10] neu_img_h 5/16
- 2026-07-31 18:38:46 RUNNING pid=18880 hb_age_s=0 stage=neu_img_h:L20 :: [18:31:44] neu_img_h 4/16 | [18:36:10] neu_img_h 5/16
- 2026-07-31 18:40:46 RUNNING pid=18880 hb_age_s=2 stage=neu_img_h:L1 :: [18:36:10] neu_img_h 5/16 | [18:40:35] neu_img_h 6/16
- 2026-07-31 18:42:46 RUNNING pid=18880 hb_age_s=6 stage=neu_img_h:L16 :: [18:36:10] neu_img_h 5/16 | [18:40:35] neu_img_h 6/16
- 2026-07-31 18:44:47 RUNNING pid=18880 hb_age_s=3 stage=neu_img_h:L32 :: [18:36:10] neu_img_h 5/16 | [18:40:35] neu_img_h 6/16
- 2026-07-31 18:46:47 RUNNING pid=18880 hb_age_s=0 stage=neu_img_h:L14 :: [18:40:35] neu_img_h 6/16 | [18:44:59] neu_img_h 7/16
- 2026-07-31 18:48:47 RUNNING pid=18880 hb_age_s=4 stage=neu_img_h:L29 :: [18:40:35] neu_img_h 6/16 | [18:44:59] neu_img_h 7/16
- 2026-07-31 18:50:47 RUNNING pid=18880 hb_age_s=1 stage=neu_img_h:L11 :: [18:44:59] neu_img_h 7/16 | [18:49:21] neu_img_h 8/16
- 2026-07-31 18:52:48 RUNNING pid=18880 hb_age_s=5 stage=neu_img_h:L26 :: [18:44:59] neu_img_h 7/16 | [18:49:21] neu_img_h 8/16
- 2026-07-31 18:54:48 RUNNING pid=18880 hb_age_s=1 stage=neu_img_h:L8 :: [18:49:21] neu_img_h 8/16 | [18:53:45] neu_img_h 9/16
- 2026-07-31 18:56:48 RUNNING pid=18880 hb_age_s=1 stage=neu_img_h:L23 :: [18:49:21] neu_img_h 8/16 | [18:53:45] neu_img_h 9/16
- 2026-07-31 18:58:49 RUNNING pid=18880 hb_age_s=2 stage=neu_img_h:L4 :: [18:53:45] neu_img_h 9/16 | [18:58:15] neu_img_h 10/16
- 2026-07-31 19:00:49 RUNNING pid=18880 hb_age_s=1 stage=neu_img_h:L19 :: [18:53:45] neu_img_h 9/16 | [18:58:15] neu_img_h 10/16
- 2026-07-31 19:02:49 RUNNING pid=18880 hb_age_s=5 stage=neu_img_h:L0 :: [18:58:15] neu_img_h 10/16 | [19:02:43] neu_img_h 11/16
- 2026-07-31 19:04:49 RUNNING pid=18880 hb_age_s=5 stage=neu_img_h:L16 :: [18:58:15] neu_img_h 10/16 | [19:02:43] neu_img_h 11/16
- 2026-07-31 19:06:49 RUNNING pid=18880 hb_age_s=5 stage=neu_img_h:L32 :: [18:58:15] neu_img_h 10/16 | [19:02:43] neu_img_h 11/16
- 2026-07-31 19:08:50 RUNNING pid=18880 hb_age_s=5 stage=neu_img_h:L14 :: [19:02:43] neu_img_h 11/16 | [19:06:59] neu_img_h 12/16
- 2026-07-31 19:10:50 RUNNING pid=18880 hb_age_s=5 stage=neu_img_h:L30 :: [19:02:43] neu_img_h 11/16 | [19:06:59] neu_img_h 12/16
- 2026-07-31 19:12:50 RUNNING pid=18880 hb_age_s=4 stage=neu_img_h:L12 :: [19:06:59] neu_img_h 12/16 | [19:11:15] neu_img_h 13/16
- 2026-07-31 19:14:50 RUNNING pid=18880 hb_age_s=4 stage=neu_img_h:L28 :: [19:06:59] neu_img_h 12/16 | [19:11:15] neu_img_h 13/16
- 2026-07-31 19:16:50 RUNNING pid=18880 hb_age_s=5 stage=neu_img_h:L9 :: [19:11:15] neu_img_h 13/16 | [19:15:31] neu_img_h 14/16
- 2026-07-31 19:18:51 RUNNING pid=18880 hb_age_s=6 stage=neu_img_h:L24 :: [19:11:15] neu_img_h 13/16 | [19:15:31] neu_img_h 14/16
- 2026-07-31 19:20:51 RUNNING pid=18880 hb_age_s=0 stage=neu_img_h:L6 :: [19:15:31] neu_img_h 14/16 | [19:20:04] neu_img_h 15/16
- 2026-07-31 19:22:51 RUNNING pid=18880 hb_age_s=4 stage=neu_img_h:L21 :: [19:15:31] neu_img_h 14/16 | [19:20:04] neu_img_h 15/16
- 2026-07-31 19:24:51 RUNNING pid=18880 hb_age_s=11 stage=beh:no_image :: [19:24:40] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [19:24:40] beh no_image 1/24
- 2026-07-31 19:26:52 RUNNING pid=18880 hb_age_s=12 stage=beh:no_image :: [19:26:40] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [19:26:40] beh no_image 10/24
- 2026-07-31 19:28:52 RUNNING pid=18880 hb_age_s=5 stage=beh:no_image :: [19:28:46] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [19:28:46] beh no_image 20/24
- 2026-07-31 19:30:52 RUNNING pid=18880 hb_age_s=6 stage=beh:negative :: [19:30:45] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [19:30:45] beh negative 3/12
- 2026-07-31 19:32:52 RUNNING pid=18880 hb_age_s=3 stage=beh:negative :: [19:32:48] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [19:32:48] beh negative 8/12
- 2026-07-31 19:34:53 RUNNING pid=18880 hb_age_s=14 stage=beh:neutral :: [19:34:39] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [19:34:39] beh neutral 1/12
- 2026-07-31 19:36:53 RUNNING pid=18880 hb_age_s=1 stage=beh:neutral :: [19:36:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [19:36:51] beh neutral 7/12
- 2026-07-31 19:38:54 RUNNING pid=18880 hb_age_s=13 stage=caption :: [19:38:41] PHASE_E_STEP3_GAP | [19:38:41] caption 0/16
- 2026-07-31 19:40:54 RUNNING pid=18880 hb_age_s=16 stage=caption :: [19:40:38] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [19:40:38] caption 5/16
- 2026-07-31 19:42:54 RUNNING pid=18880 hb_age_s=3 stage=caption :: [19:42:50] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [19:42:50] caption 11/16
- 2026-07-31 19:44:54 RUNNING pid=18880 hb_age_s=0 stage=gap_img:L0 :: [19:44:54] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [19:44:54] gap_img 0/16
- 2026-07-31 19:46:54 RUNNING pid=18880 hb_age_s=1 stage=gap_img:L14 :: [19:44:54] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [19:44:54] gap_img 0/16
- 2026-07-31 19:48:55 RUNNING pid=18880 hb_age_s=3 stage=gap_img:L29 :: [19:44:54] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [19:44:54] gap_img 0/16
- 2026-07-31 19:50:55 RUNNING pid=18880 hb_age_s=3 stage=gap_img:L10 :: [19:44:54] gap_img 0/16 | [19:49:32] gap_img 1/16
- 2026-07-31 19:52:55 RUNNING pid=18880 hb_age_s=3 stage=gap_img:L25 :: [19:44:54] gap_img 0/16 | [19:49:32] gap_img 1/16
- 2026-07-31 19:54:55 RUNNING pid=18880 hb_age_s=6 stage=gap_img:L6 :: [19:49:32] gap_img 1/16 | [19:54:03] gap_img 2/16
- 2026-07-31 19:56:56 RUNNING pid=18880 hb_age_s=2 stage=gap_img:L22 :: [19:49:32] gap_img 1/16 | [19:54:03] gap_img 2/16
- 2026-07-31 19:58:56 RUNNING pid=18880 hb_age_s=6 stage=gap_img:L3 :: [19:54:03] gap_img 2/16 | [19:58:26] gap_img 3/16
- 2026-07-31 20:00:56 RUNNING pid=18880 hb_age_s=1 stage=gap_img:L19 :: [19:54:03] gap_img 2/16 | [19:58:26] gap_img 3/16
- 2026-07-31 20:02:56 RUNNING pid=18880 hb_age_s=4 stage=gap_img:L0 :: [19:58:26] gap_img 3/16 | [20:02:51] gap_img 4/16
- 2026-07-31 20:04:57 RUNNING pid=18880 hb_age_s=1 stage=gap_img:L16 :: [19:58:26] gap_img 3/16 | [20:02:51] gap_img 4/16
- 2026-07-31 20:06:57 RUNNING pid=18880 hb_age_s=4 stage=gap_img:L31 :: [19:58:26] gap_img 3/16 | [20:02:51] gap_img 4/16
- 2026-07-31 20:08:57 RUNNING pid=18880 hb_age_s=0 stage=gap_img:L13 :: [20:02:51] gap_img 4/16 | [20:07:15] gap_img 5/16
- 2026-07-31 20:10:57 RUNNING pid=18880 hb_age_s=3 stage=gap_img:L28 :: [20:02:51] gap_img 4/16 | [20:07:15] gap_img 5/16
- 2026-07-31 20:12:58 RUNNING pid=18880 hb_age_s=0 stage=gap_img:L10 :: [20:07:15] gap_img 5/16 | [20:11:40] gap_img 6/16
- 2026-07-31 20:14:58 RUNNING pid=18880 hb_age_s=4 stage=gap_img:L25 :: [20:07:15] gap_img 5/16 | [20:11:40] gap_img 6/16
- 2026-07-31 20:16:58 RUNNING pid=18880 hb_age_s=5 stage=gap_img:L6 :: [20:11:40] gap_img 6/16 | [20:16:06] gap_img 7/16
- 2026-07-31 20:18:58 RUNNING pid=18880 hb_age_s=1 stage=gap_img:L22 :: [20:11:40] gap_img 6/16 | [20:16:06] gap_img 7/16
- 2026-07-31 20:20:58 RUNNING pid=18880 hb_age_s=4 stage=gap_img:L3 :: [20:16:06] gap_img 7/16 | [20:20:31] gap_img 8/16
- 2026-07-31 20:22:59 RUNNING pid=18880 hb_age_s=3 stage=gap_img:L19 :: [20:16:06] gap_img 7/16 | [20:20:31] gap_img 8/16
- 2026-07-31 20:24:59 RUNNING pid=18880 hb_age_s=3 stage=gap_img:L1 :: [20:20:31] gap_img 8/16 | [20:24:48] gap_img 9/16
- 2026-07-31 20:26:59 RUNNING pid=18880 hb_age_s=2 stage=gap_img:L17 :: [20:20:31] gap_img 8/16 | [20:24:48] gap_img 9/16
- 2026-07-31 20:28:59 RUNNING pid=18880 hb_age_s=2 stage=gap_img:L33 :: [20:20:31] gap_img 8/16 | [20:24:48] gap_img 9/16
- 2026-07-31 20:31:00 RUNNING pid=18880 hb_age_s=2 stage=gap_img:L15 :: [20:24:48] gap_img 9/16 | [20:29:04] gap_img 10/16
- 2026-07-31 20:33:00 RUNNING pid=18880 hb_age_s=1 stage=gap_img:L31 :: [20:24:48] gap_img 9/16 | [20:29:04] gap_img 10/16
- 2026-07-31 20:35:00 RUNNING pid=18880 hb_age_s=1 stage=gap_img:L13 :: [20:29:04] gap_img 10/16 | [20:33:21] gap_img 11/16
- 2026-07-31 20:37:00 RUNNING pid=18880 hb_age_s=2 stage=gap_img:L28 :: [20:29:04] gap_img 10/16 | [20:33:21] gap_img 11/16
- 2026-07-31 20:39:01 RUNNING pid=18880 hb_age_s=6 stage=gap_img:L9 :: [20:33:21] gap_img 11/16 | [20:37:44] gap_img 12/16
- 2026-07-31 20:41:01 RUNNING pid=18880 hb_age_s=0 stage=gap_img:L25 :: [20:33:21] gap_img 11/16 | [20:37:44] gap_img 12/16
- 2026-07-31 20:43:01 RUNNING pid=18880 hb_age_s=4 stage=gap_img:L6 :: [20:37:44] gap_img 12/16 | [20:42:10] gap_img 13/16
- 2026-07-31 20:45:01 RUNNING pid=18880 hb_age_s=7 stage=gap_img:L21 :: [20:37:44] gap_img 12/16 | [20:42:10] gap_img 13/16
- 2026-07-31 20:47:01 RUNNING pid=18880 hb_age_s=7 stage=gap_img:L2 :: [20:42:10] gap_img 13/16 | [20:46:38] gap_img 14/16
- 2026-07-31 20:49:02 RUNNING pid=18880 hb_age_s=2 stage=gap_img:L17 :: [20:42:10] gap_img 13/16 | [20:46:38] gap_img 14/16
- 2026-07-31 20:51:02 RUNNING pid=18880 hb_age_s=0 stage=gap_img:L31 :: [20:42:10] gap_img 13/16 | [20:46:38] gap_img 14/16
- 2026-07-31 20:53:02 RUNNING pid=18880 hb_age_s=6 stage=gap_img:L11 :: [20:46:38] gap_img 14/16 | [20:51:27] gap_img 15/16
- 2026-07-31 20:55:02 RUNNING pid=18880 hb_age_s=1 stage=gap_img:L27 :: [20:46:38] gap_img 14/16 | [20:51:27] gap_img 15/16
- 2026-07-31 20:57:03 RUNNING pid=18880 hb_age_s=6 stage=gap_neu:L7 :: [20:51:27] gap_img 15/16 | [20:56:02] gap_neu 0/16
- 2026-07-31 20:59:03 RUNNING pid=18880 hb_age_s=5 stage=gap_neu:L23 :: [20:51:27] gap_img 15/16 | [20:56:02] gap_neu 0/16
- 2026-07-31 21:01:03 RUNNING pid=18880 hb_age_s=3 stage=gap_neu:L2 :: [20:56:02] gap_neu 0/16 | [21:00:44] gap_neu 1/16
- 2026-07-31 21:03:04 RUNNING pid=18880 hb_age_s=0 stage=gap_neu:L18 :: [20:56:02] gap_neu 0/16 | [21:00:44] gap_neu 1/16
- 2026-07-31 21:05:04 RUNNING pid=18880 hb_age_s=0 stage=gap_neu:L29 :: [20:56:02] gap_neu 0/16 | [21:00:44] gap_neu 1/16
- 2026-07-31 21:07:04 RUNNING pid=18880 hb_age_s=6 stage=gap_neu:L8 :: [21:00:44] gap_neu 1/16 | [21:05:40] gap_neu 2/16
- 2026-07-31 21:09:05 RUNNING pid=18880 hb_age_s=1 stage=gap_neu:L25 :: [21:00:44] gap_neu 1/16 | [21:05:40] gap_neu 2/16
- 2026-07-31 21:11:05 RUNNING pid=18880 hb_age_s=7 stage=gap_neu:L4 :: [21:05:40] gap_neu 2/16 | [21:10:08] gap_neu 3/16
- 2026-07-31 21:13:05 RUNNING pid=18880 hb_age_s=5 stage=gap_neu:L18 :: [21:05:40] gap_neu 2/16 | [21:10:08] gap_neu 3/16
- 2026-07-31 21:15:05 RUNNING pid=18880 hb_age_s=-1 stage=gap_neu:L32 :: [21:05:40] gap_neu 2/16 | [21:10:08] gap_neu 3/16
- 2026-07-31 21:17:05 RUNNING pid=18880 hb_age_s=3 stage=gap_neu:L13 :: [21:10:08] gap_neu 3/16 | [21:15:22] gap_neu 4/16
- 2026-07-31 21:19:06 RUNNING pid=18880 hb_age_s=0 stage=gap_neu:L26 :: [21:10:08] gap_neu 3/16 | [21:15:22] gap_neu 4/16
- 2026-07-31 21:21:06 RUNNING pid=18880 hb_age_s=4 stage=gap_neu:L4 :: [21:15:22] gap_neu 4/16 | [21:20:09] gap_neu 5/16
- 2026-07-31 21:23:06 RUNNING pid=18880 hb_age_s=4 stage=gap_neu:L20 :: [21:15:22] gap_neu 4/16 | [21:20:09] gap_neu 5/16
- 2026-07-31 21:25:06 RUNNING pid=18880 hb_age_s=2 stage=gap_neu:L0 :: [21:20:09] gap_neu 5/16 | [21:25:04] gap_neu 6/16
- 2026-07-31 21:27:07 RUNNING pid=18880 hb_age_s=0 stage=gap_neu:L17 :: [21:20:09] gap_neu 5/16 | [21:25:04] gap_neu 6/16
- 2026-07-31 21:29:07 RUNNING pid=18880 hb_age_s=0 stage=gap_neu:L0 :: [21:25:04] gap_neu 6/16 | [21:29:06] gap_neu 7/16
- 2026-07-31 21:31:07 RUNNING pid=18880 hb_age_s=0 stage=gap_neu:L17 :: [21:25:04] gap_neu 6/16 | [21:29:06] gap_neu 7/16
- 2026-07-31 21:33:07 RUNNING pid=18880 hb_age_s=-1 stage=gap_neu:L31 :: [21:25:04] gap_neu 6/16 | [21:29:06] gap_neu 7/16
- 2026-07-31 21:35:08 RUNNING pid=18880 hb_age_s=4 stage=gap_neu:L13 :: [21:29:06] gap_neu 7/16 | [21:33:30] gap_neu 8/16
- 2026-07-31 21:37:08 RUNNING pid=18880 hb_age_s=18 stage=gap_neu:L26 :: [21:29:06] gap_neu 7/16 | [21:33:30] gap_neu 8/16
- 2026-07-31 21:39:08 RUNNING pid=18880 hb_age_s=0 stage=gap_neu:L7 :: [21:33:30] gap_neu 8/16 | [21:38:14] gap_neu 9/16
- 2026-07-31 21:41:08 RUNNING pid=18880 hb_age_s=0 stage=gap_neu:L18 :: [21:33:30] gap_neu 8/16 | [21:38:14] gap_neu 9/16
- 2026-07-31 21:43:09 RUNNING pid=18880 hb_age_s=6 stage=gap_neu:L33 :: [21:33:30] gap_neu 8/16 | [21:38:14] gap_neu 9/16
- 2026-07-31 21:45:09 RUNNING pid=18880 hb_age_s=1 stage=gap_neu:L16 :: [21:38:14] gap_neu 9/16 | [21:43:11] gap_neu 10/16
- 2026-07-31 21:47:09 RUNNING pid=18880 hb_age_s=2 stage=gap_neu:L31 :: [21:38:14] gap_neu 9/16 | [21:43:11] gap_neu 10/16
- 2026-07-31 21:49:09 RUNNING pid=18880 hb_age_s=0 stage=gap_neu:L11 :: [21:43:11] gap_neu 10/16 | [21:47:49] gap_neu 11/16
- 2026-07-31 21:51:10 RUNNING pid=18880 hb_age_s=6 stage=gap_neu:L23 :: [21:43:11] gap_neu 10/16 | [21:47:49] gap_neu 11/16
- 2026-07-31 21:53:10 RUNNING pid=18880 hb_age_s=4 stage=gap_neu:L0 :: [21:47:49] gap_neu 11/16 | [21:53:05] gap_neu 12/16
- 2026-07-31 21:55:10 RUNNING pid=18880 hb_age_s=6 stage=gap_neu:L9 :: [21:47:49] gap_neu 11/16 | [21:53:05] gap_neu 12/16
- 2026-07-31 21:57:10 RUNNING pid=18880 hb_age_s=5 stage=gap_neu:L17 :: [21:47:49] gap_neu 11/16 | [21:53:05] gap_neu 12/16
- 2026-07-31 21:59:10 RUNNING pid=18880 hb_age_s=1 stage=gap_neu:L32 :: [21:47:49] gap_neu 11/16 | [21:53:05] gap_neu 12/16
- 2026-07-31 22:01:11 RUNNING pid=18880 hb_age_s=0 stage=gap_neu:L13 :: [21:53:05] gap_neu 12/16 | [21:59:25] gap_neu 13/16
- 2026-07-31 22:03:11 RUNNING pid=18880 hb_age_s=5 stage=gap_neu:L29 :: [21:53:05] gap_neu 12/16 | [21:59:25] gap_neu 13/16
- 2026-07-31 22:05:11 RUNNING pid=18880 hb_age_s=5 stage=gap_neu:L7 :: [21:59:25] gap_neu 13/16 | [22:03:40] gap_neu 14/16
- 2026-07-31 22:07:11 RUNNING pid=18880 hb_age_s=1 stage=gap_neu:L21 :: [21:59:25] gap_neu 13/16 | [22:03:40] gap_neu 14/16
- 2026-07-31 22:09:12 RUNNING pid=18880 hb_age_s=2 stage=gap_neu:L32 :: [21:59:25] gap_neu 13/16 | [22:03:40] gap_neu 14/16
- 2026-07-31 22:11:12 RUNNING pid=18880 hb_age_s=5 stage=gap_neu:L11 :: [22:03:40] gap_neu 14/16 | [22:09:24] gap_neu 15/16
- 2026-07-31 22:13:12 RUNNING pid=18880 hb_age_s=0 stage=gap_neu:L22 :: [22:03:40] gap_neu 14/16 | [22:09:24] gap_neu 15/16
- 2026-07-31 22:15:12 RUNNING pid=18880 hb_age_s=20 stage=gap_neu:L33 :: [22:14:59] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:14:59] PHASE_F_STEP4_THRESHOLD
- 2026-07-31 22:17:13 RUNNING pid=18880 hb_age_s=141 stage=gap_neu:L33 :: [22:16:44] gamma=20 refuse=0.00 rand=1.00 coherent=False | [22:17:01] gamma=50 refuse=0.00 rand=1.00 coherent=False
- 2026-07-31 22:19:13 RUNNING pid=18880 hb_age_s=1 stage=resid:L13 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:21:13 RUNNING pid=18880 hb_age_s=1 stage=resid:L23 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:23:13 RUNNING pid=18880 hb_age_s=6 stage=resid:L1 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:25:14 RUNNING pid=18880 hb_age_s=4 stage=resid:L18 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:27:14 RUNNING pid=18880 hb_age_s=1 stage=resid:L0 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:29:14 RUNNING pid=18880 hb_age_s=6 stage=resid:L13 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:31:14 RUNNING pid=18880 hb_age_s=1 stage=resid:L28 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:33:15 RUNNING pid=18880 hb_age_s=6 stage=resid:L10 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:35:15 RUNNING pid=18880 hb_age_s=0 stage=resid:L28 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:37:15 RUNNING pid=18880 hb_age_s=2 stage=resid:L7 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:41:16 RUNNING pid=18880 hb_age_s=2 stage=resid:L3 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:43:16 RUNNING pid=18880 hb_age_s=5 stage=resid:L15 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:45:16 RUNNING pid=18880 hb_age_s=6 stage=resid:L32 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:47:16 RUNNING pid=18880 hb_age_s=2 stage=resid:L12 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:49:17 RUNNING pid=18880 hb_age_s=4 stage=resid:L29 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:51:17 RUNNING pid=18880 hb_age_s=6 stage=resid:L8 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:53:17 RUNNING pid=18880 hb_age_s=0 stage=resid:L26 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:55:17 RUNNING pid=18880 hb_age_s=4 stage=resid:L5 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:57:17 RUNNING pid=18880 hb_age_s=6 stage=resid:L19 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 22:59:18 RUNNING pid=18880 hb_age_s=0 stage=resid:L29 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:01:18 RUNNING pid=18880 hb_age_s=5 stage=resid:L10 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:03:18 RUNNING pid=18880 hb_age_s=21 stage=resid:L24 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:05:18 RUNNING pid=18880 hb_age_s=5 stage=resid:L3 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:07:19 RUNNING pid=18880 hb_age_s=3 stage=resid:L20 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:09:19 RUNNING pid=18880 hb_age_s=6 stage=resid:L2 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:11:19 RUNNING pid=18880 hb_age_s=14 stage=resid:L18 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:13:19 RUNNING pid=18880 hb_age_s=2 stage=resid:L33 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:15:19 RUNNING pid=18880 hb_age_s=3 stage=resid:L13 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:17:20 RUNNING pid=18880 hb_age_s=3 stage=resid:L28 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:19:20 RUNNING pid=18880 hb_age_s=5 stage=resid:L1 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:21:20 RUNNING pid=18880 hb_age_s=0 stage=resid:L18 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:23:20 RUNNING pid=18880 hb_age_s=3 stage=resid:L29 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:25:21 RUNNING pid=18880 hb_age_s=5 stage=resid:L5 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:27:21 RUNNING pid=18880 hb_age_s=3 stage=resid:L21 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:29:21 RUNNING pid=18880 hb_age_s=29 stage=resid:L27 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:31:21 RUNNING pid=18880 hb_age_s=-1 stage=resid:L8 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:33:21 RUNNING pid=18880 hb_age_s=-1 stage=resid:L20 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:35:22 RUNNING pid=18880 hb_age_s=6 stage=resid:L33 :: [22:17:22] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [22:17:22] PHASE_G_STEP5_LAYERS
- 2026-07-31 23:37:22 RUNNING pid=18880 hb_age_s=5 stage=resid:L14 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 23:39:22 RUNNING pid=18880 hb_age_s=2 stage=resid:L25 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 23:41:22 RUNNING pid=18880 hb_age_s=6 stage=resid:L7 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 23:43:23 RUNNING pid=18880 hb_age_s=5 stage=resid:L17 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 23:45:23 RUNNING pid=18880 hb_age_s=1 stage=resid:L28 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 23:47:23 RUNNING pid=18880 hb_age_s=3 stage=resid:L9 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 23:49:23 RUNNING pid=18880 hb_age_s=2 stage=resid:L22 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 23:51:23 RUNNING pid=18880 hb_age_s=2 stage=resid:L0 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 23:53:24 RUNNING pid=18880 hb_age_s=2 stage=resid:L9 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 23:55:24 RUNNING pid=18880 hb_age_s=25 stage=resid:L13 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 23:57:24 RUNNING pid=18880 hb_age_s=22 stage=resid:L24 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-07-31 23:59:25 RUNNING pid=18880 hb_age_s=5 stage=resid:L0 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:01:25 RUNNING pid=18880 hb_age_s=21 stage=resid:L14 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:03:25 RUNNING pid=18880 hb_age_s=18 stage=resid:L28 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:05:25 RUNNING pid=18880 hb_age_s=1 stage=resid:L2 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:07:25 RUNNING pid=18880 hb_age_s=1 stage=resid:L18 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:09:26 RUNNING pid=18880 hb_age_s=6 stage=resid:L0 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:11:26 RUNNING pid=18880 hb_age_s=2 stage=resid:L14 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:13:26 RUNNING pid=18880 hb_age_s=1 stage=resid:L31 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:15:26 RUNNING pid=18880 hb_age_s=2 stage=resid:L10 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:17:27 RUNNING pid=18880 hb_age_s=7 stage=resid:L18 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:19:27 RUNNING pid=18880 hb_age_s=6 stage=resid:L28 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:21:27 RUNNING pid=18880 hb_age_s=5 stage=resid:L11 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:23:27 RUNNING pid=18880 hb_age_s=1 stage=resid:L21 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:25:28 RUNNING pid=18880 hb_age_s=0 stage=resid:L4 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:27:28 RUNNING pid=18880 hb_age_s=6 stage=resid:L14 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:29:28 RUNNING pid=18880 hb_age_s=6 stage=resid:L31 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:31:28 RUNNING pid=18880 hb_age_s=5 stage=resid:L14 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:33:28 RUNNING pid=18880 hb_age_s=6 stage=resid:L28 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:35:29 RUNNING pid=18880 hb_age_s=4 stage=resid:L11 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:37:29 RUNNING pid=18880 hb_age_s=0 stage=resid:L26 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:39:29 RUNNING pid=18880 hb_age_s=0 stage=resid:L8 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:41:30 RUNNING pid=18880 hb_age_s=1 stage=resid:L22 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:43:30 RUNNING pid=18880 hb_age_s=6 stage=resid:L4 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:45:30 RUNNING pid=18880 hb_age_s=4 stage=resid:L18 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:47:30 RUNNING pid=18880 hb_age_s=2 stage=resid:L1 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:49:30 RUNNING pid=18880 hb_age_s=3 stage=resid:L14 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:51:31 RUNNING pid=18880 hb_age_s=5 stage=resid:L31 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:53:31 RUNNING pid=18880 hb_age_s=3 stage=resid:L14 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:55:31 RUNNING pid=18880 hb_age_s=4 stage=resid:L28 :: [23:35:27] layer 0: imgΔ=6.97 txtΔ=-3.48 | [23:35:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:57:31 RUNNING pid=18880 hb_age_s=7 stage=resid:L2 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 00:59:32 RUNNING pid=18880 hb_age_s=1 stage=resid:L13 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:01:32 RUNNING pid=18880 hb_age_s=2 stage=resid:L26 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:03:32 RUNNING pid=18880 hb_age_s=9 stage=resid:L7 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:05:32 RUNNING pid=18880 hb_age_s=5 stage=resid:L20 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:07:32 RUNNING pid=18880 hb_age_s=7 stage=resid:L33 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:09:33 RUNNING pid=18880 hb_age_s=6 stage=resid:L15 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:11:33 RUNNING pid=18880 hb_age_s=3 stage=resid:L29 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:13:33 RUNNING pid=18880 hb_age_s=6 stage=resid:L4 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:15:33 RUNNING pid=18880 hb_age_s=6 stage=resid:L20 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:17:34 RUNNING pid=18880 hb_age_s=7 stage=resid:L32 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:19:34 RUNNING pid=18880 hb_age_s=1 stage=resid:L15 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:21:34 RUNNING pid=18880 hb_age_s=1 stage=resid:L29 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:23:34 RUNNING pid=18880 hb_age_s=4 stage=resid:L12 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:25:34 RUNNING pid=18880 hb_age_s=4 stage=resid:L29 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:27:35 RUNNING pid=18880 hb_age_s=5 stage=resid:L9 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:29:35 RUNNING pid=18880 hb_age_s=2 stage=resid:L27 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:31:35 RUNNING pid=18880 hb_age_s=2 stage=resid:L10 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:33:35 RUNNING pid=18880 hb_age_s=5 stage=resid:L27 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:35:36 RUNNING pid=18880 hb_age_s=2 stage=resid:L7 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:37:36 RUNNING pid=18880 hb_age_s=3 stage=resid:L23 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:39:36 RUNNING pid=18880 hb_age_s=3 stage=resid:L5 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:41:36 RUNNING pid=18880 hb_age_s=4 stage=resid:L18 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:43:37 RUNNING pid=18880 hb_age_s=5 stage=resid:L1 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:45:37 RUNNING pid=18880 hb_age_s=3 stage=resid:L18 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:47:37 RUNNING pid=18880 hb_age_s=6 stage=resid:L32 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:49:37 RUNNING pid=18880 hb_age_s=1 stage=resid:L13 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:51:37 RUNNING pid=18880 hb_age_s=16 stage=resid:L25 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:53:38 RUNNING pid=18880 hb_age_s=4 stage=resid:L7 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:55:38 RUNNING pid=18880 hb_age_s=6 stage=resid:L21 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:57:38 RUNNING pid=18880 hb_age_s=32 stage=resid:L30 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 01:59:38 RUNNING pid=18880 hb_age_s=10 stage=resid:L8 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:01:39 RUNNING pid=18880 hb_age_s=0 stage=resid:L19 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:03:39 RUNNING pid=18880 hb_age_s=11 stage=resid:L0 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:05:39 RUNNING pid=18880 hb_age_s=1 stage=resid:L15 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:07:39 RUNNING pid=18880 hb_age_s=-1 stage=resid:L32 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:09:40 RUNNING pid=18880 hb_age_s=1 stage=resid:L15 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:11:40 RUNNING pid=18880 hb_age_s=1 stage=resid:L28 :: [00:56:51] layer 5: imgΔ=298.33 txtΔ=7.80 | [00:56:51] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:13:40 RUNNING pid=18880 hb_age_s=3 stage=resid:L10 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:15:40 RUNNING pid=18880 hb_age_s=6 stage=resid:L24 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:17:41 RUNNING pid=18880 hb_age_s=4 stage=resid:L2 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:19:41 RUNNING pid=18880 hb_age_s=2 stage=resid:L18 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:21:41 RUNNING pid=18880 hb_age_s=6 stage=resid:L26 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:23:41 RUNNING pid=18880 hb_age_s=4 stage=resid:L7 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:25:42 RUNNING pid=18880 hb_age_s=0 stage=resid:L25 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:27:42 RUNNING pid=18880 hb_age_s=3 stage=resid:L8 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:29:42 RUNNING pid=18880 hb_age_s=0 stage=resid:L26 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:31:42 RUNNING pid=18880 hb_age_s=2 stage=resid:L9 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:33:43 RUNNING pid=18880 hb_age_s=5 stage=resid:L25 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:35:43 RUNNING pid=18880 hb_age_s=7 stage=resid:L5 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:37:43 RUNNING pid=18880 hb_age_s=5 stage=resid:L21 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:39:43 RUNNING pid=18880 hb_age_s=1 stage=resid:L4 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:41:43 RUNNING pid=18880 hb_age_s=4 stage=resid:L20 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:43:44 RUNNING pid=18880 hb_age_s=6 stage=resid:L33 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:45:44 RUNNING pid=18880 hb_age_s=0 stage=resid:L17 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:47:44 RUNNING pid=18880 hb_age_s=3 stage=resid:L31 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:49:44 RUNNING pid=18880 hb_age_s=6 stage=resid:L13 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:51:44 RUNNING pid=18880 hb_age_s=5 stage=resid:L29 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:53:45 RUNNING pid=18880 hb_age_s=1 stage=resid:L13 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:55:45 RUNNING pid=18880 hb_age_s=8 stage=resid:L26 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:57:45 RUNNING pid=18880 hb_age_s=29 stage=resid:L33 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 02:59:45 RUNNING pid=18880 hb_age_s=0 stage=resid:L7 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:01:46 RUNNING pid=18880 hb_age_s=11 stage=resid:L22 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:03:46 RUNNING pid=18880 hb_age_s=6 stage=resid:L2 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:05:46 RUNNING pid=18880 hb_age_s=6 stage=resid:L15 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:07:46 RUNNING pid=18880 hb_age_s=9 stage=resid:L31 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:09:46 RUNNING pid=18880 hb_age_s=0 stage=resid:L6 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:11:47 RUNNING pid=18880 hb_age_s=2 stage=resid:L23 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:13:47 RUNNING pid=18880 hb_age_s=5 stage=resid:L2 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:15:47 RUNNING pid=18880 hb_age_s=6 stage=resid:L14 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:17:47 RUNNING pid=18880 hb_age_s=5 stage=resid:L30 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:19:48 RUNNING pid=18880 hb_age_s=8 stage=resid:L9 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:21:48 RUNNING pid=18880 hb_age_s=4 stage=resid:L17 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:23:48 RUNNING pid=18880 hb_age_s=0 stage=resid:L1 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:25:48 RUNNING pid=18880 hb_age_s=5 stage=resid:L13 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:27:49 RUNNING pid=18880 hb_age_s=2 stage=resid:L24 :: [02:12:27] layer 10: imgΔ=831.92 txtΔ=26.01 | [02:12:27] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:29:49 RUNNING pid=18880 hb_age_s=5 stage=resid:L6 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:31:49 RUNNING pid=18880 hb_age_s=0 stage=resid:L21 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:33:49 RUNNING pid=18880 hb_age_s=1 stage=resid:L4 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:35:50 RUNNING pid=18880 hb_age_s=3 stage=resid:L17 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:37:50 RUNNING pid=18880 hb_age_s=0 stage=resid:L27 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:39:50 RUNNING pid=18880 hb_age_s=25 stage=resid:L3 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:41:50 RUNNING pid=18880 hb_age_s=4 stage=resid:L19 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:43:50 RUNNING pid=18880 hb_age_s=2 stage=resid:L33 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:45:51 RUNNING pid=18880 hb_age_s=3 stage=resid:L16 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:47:51 RUNNING pid=18880 hb_age_s=1 stage=resid:L33 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:49:51 RUNNING pid=18880 hb_age_s=1 stage=resid:L16 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:51:52 RUNNING pid=18880 hb_age_s=5 stage=resid:L30 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:53:52 RUNNING pid=18880 hb_age_s=1 stage=resid:L14 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:55:52 RUNNING pid=18880 hb_age_s=4 stage=resid:L27 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:57:52 RUNNING pid=18880 hb_age_s=2 stage=resid:L9 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 03:59:53 RUNNING pid=18880 hb_age_s=17 stage=resid:L19 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:01:53 RUNNING pid=18880 hb_age_s=1 stage=resid:L29 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:03:53 RUNNING pid=18880 hb_age_s=12 stage=resid:L8 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:05:53 RUNNING pid=18880 hb_age_s=6 stage=resid:L20 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:07:53 RUNNING pid=18880 hb_age_s=27 stage=resid:L0 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:09:54 RUNNING pid=18880 hb_age_s=1 stage=resid:L14 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:11:54 RUNNING pid=18880 hb_age_s=11 stage=resid:L29 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:13:54 RUNNING pid=18880 hb_age_s=19 stage=resid:L10 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:15:54 RUNNING pid=18880 hb_age_s=13 stage=resid:L21 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:17:55 RUNNING pid=18880 hb_age_s=4 stage=resid:L29 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:19:55 RUNNING pid=18880 hb_age_s=9 stage=resid:L9 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:21:55 RUNNING pid=18880 hb_age_s=8 stage=resid:L22 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:23:55 RUNNING pid=18880 hb_age_s=1 stage=resid:L3 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:25:55 RUNNING pid=18880 hb_age_s=2 stage=resid:L20 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:27:56 RUNNING pid=18880 hb_age_s=3 stage=resid:L0 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:29:56 RUNNING pid=18880 hb_age_s=4 stage=resid:L17 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:31:56 RUNNING pid=18880 hb_age_s=5 stage=resid:L31 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:33:56 RUNNING pid=18880 hb_age_s=4 stage=resid:L14 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:35:57 RUNNING pid=18880 hb_age_s=8 stage=resid:L29 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:37:57 RUNNING pid=18880 hb_age_s=1 stage=resid:L10 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:39:57 RUNNING pid=18880 hb_age_s=3 stage=resid:L23 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:41:57 RUNNING pid=18880 hb_age_s=2 stage=resid:L2 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:43:58 RUNNING pid=18880 hb_age_s=0 stage=resid:L19 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:45:58 RUNNING pid=18880 hb_age_s=3 stage=resid:L33 :: [03:29:03] layer 15: imgΔ=1777.12 txtΔ=-43.78 | [03:29:03] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:47:58 RUNNING pid=18880 hb_age_s=5 stage=resid:L13 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:49:58 RUNNING pid=18880 hb_age_s=3 stage=resid:L27 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:51:58 RUNNING pid=18880 hb_age_s=-1 stage=resid:L11 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:53:59 RUNNING pid=18880 hb_age_s=4 stage=resid:L27 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:55:59 RUNNING pid=18880 hb_age_s=7 stage=resid:L8 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:57:59 RUNNING pid=18880 hb_age_s=5 stage=resid:L25 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 04:59:59 RUNNING pid=18880 hb_age_s=6 stage=resid:L4 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:02:00 RUNNING pid=18880 hb_age_s=1 stage=resid:L21 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:04:00 RUNNING pid=18880 hb_age_s=3 stage=resid:L1 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:06:00 RUNNING pid=18880 hb_age_s=4 stage=resid:L15 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:08:00 RUNNING pid=18880 hb_age_s=1 stage=resid:L29 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:10:01 RUNNING pid=18880 hb_age_s=4 stage=resid:L12 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:12:01 RUNNING pid=18880 hb_age_s=6 stage=resid:L28 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:14:01 RUNNING pid=18880 hb_age_s=28 stage=resid:L8 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:16:01 RUNNING pid=18880 hb_age_s=21 stage=resid:L16 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:18:02 RUNNING pid=18880 hb_age_s=18 stage=resid:L20 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:20:02 RUNNING pid=18880 hb_age_s=15 stage=resid:L0 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:22:02 RUNNING pid=18880 hb_age_s=8 stage=resid:L15 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:24:02 RUNNING pid=18880 hb_age_s=5 stage=resid:L32 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:26:02 RUNNING pid=18880 hb_age_s=1 stage=resid:L12 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:28:03 RUNNING pid=18880 hb_age_s=0 stage=resid:L29 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:30:03 RUNNING pid=18880 hb_age_s=7 stage=resid:L4 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:32:03 RUNNING pid=18880 hb_age_s=2 stage=resid:L21 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:34:03 RUNNING pid=18880 hb_age_s=2 stage=resid:L32 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:36:04 RUNNING pid=18880 hb_age_s=0 stage=resid:L15 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:38:04 RUNNING pid=18880 hb_age_s=4 stage=resid:L31 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:40:04 RUNNING pid=18880 hb_age_s=1 stage=resid:L11 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:42:05 RUNNING pid=18880 hb_age_s=4 stage=resid:L19 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:44:05 RUNNING pid=18880 hb_age_s=6 stage=resid:L2 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:46:05 RUNNING pid=18880 hb_age_s=6 stage=resid:L16 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:48:05 RUNNING pid=18880 hb_age_s=5 stage=resid:L33 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:50:05 RUNNING pid=18880 hb_age_s=6 stage=resid:L15 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:52:06 RUNNING pid=18880 hb_age_s=1 stage=resid:L32 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:54:06 RUNNING pid=18880 hb_age_s=4 stage=resid:L8 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:56:06 RUNNING pid=18880 hb_age_s=3 stage=resid:L25 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 05:58:06 RUNNING pid=18880 hb_age_s=3 stage=resid:L7 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:00:07 RUNNING pid=18880 hb_age_s=28 stage=resid:L16 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:02:07 RUNNING pid=18880 hb_age_s=7 stage=resid:L31 :: [04:46:05] layer 20: imgΔ=2683.87 txtΔ=-121.08 | [04:46:05] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:04:07 RUNNING pid=18880 hb_age_s=1 stage=resid:L11 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:06:08 RUNNING pid=18880 hb_age_s=1 stage=resid:L28 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:08:08 RUNNING pid=18880 hb_age_s=3 stage=resid:L8 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:10:08 RUNNING pid=18880 hb_age_s=1 stage=resid:L25 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:12:08 RUNNING pid=18880 hb_age_s=2 stage=resid:L5 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:14:08 RUNNING pid=18880 hb_age_s=5 stage=resid:L22 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:16:09 RUNNING pid=18880 hb_age_s=3 stage=resid:L2 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:18:09 RUNNING pid=18880 hb_age_s=1 stage=resid:L18 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:20:09 RUNNING pid=18880 hb_age_s=5 stage=resid:L31 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:22:09 RUNNING pid=18880 hb_age_s=30 stage=resid:L10 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:24:09 RUNNING pid=18880 hb_age_s=4 stage=resid:L27 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:26:10 RUNNING pid=18880 hb_age_s=3 stage=resid:L10 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:28:10 RUNNING pid=18880 hb_age_s=5 stage=resid:L27 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:30:10 RUNNING pid=18880 hb_age_s=3 stage=resid:L10 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:32:10 RUNNING pid=18880 hb_age_s=17 stage=resid:L25 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:34:11 RUNNING pid=18880 hb_age_s=1 stage=resid:L7 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:36:11 RUNNING pid=18880 hb_age_s=12 stage=resid:L22 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:38:11 RUNNING pid=18880 hb_age_s=5 stage=resid:L0 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:40:12 RUNNING pid=18880 hb_age_s=5 stage=resid:L12 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:42:12 RUNNING pid=18880 hb_age_s=6 stage=resid:L27 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:44:12 RUNNING pid=18880 hb_age_s=2 stage=resid:L7 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:46:12 RUNNING pid=18880 hb_age_s=4 stage=resid:L24 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:48:12 RUNNING pid=18880 hb_age_s=3 stage=resid:L5 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:50:13 RUNNING pid=18880 hb_age_s=1 stage=resid:L15 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:52:13 RUNNING pid=18880 hb_age_s=0 stage=resid:L30 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:54:13 RUNNING pid=18880 hb_age_s=0 stage=resid:L10 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:56:13 RUNNING pid=18880 hb_age_s=14 stage=resid:L22 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 06:58:14 RUNNING pid=18880 hb_age_s=0 stage=resid:L33 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 07:00:14 RUNNING pid=18880 hb_age_s=3 stage=resid:L12 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 07:02:14 RUNNING pid=18880 hb_age_s=3 stage=resid:L28 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 07:04:14 RUNNING pid=18880 hb_age_s=1 stage=resid:L4 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 07:06:15 RUNNING pid=18880 hb_age_s=3 stage=resid:L21 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 07:08:15 RUNNING pid=18880 hb_age_s=4 stage=resid:L0 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 07:10:15 RUNNING pid=18880 hb_age_s=5 stage=resid:L11 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 07:12:15 RUNNING pid=18880 hb_age_s=2 stage=resid:L27 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 07:14:15 RUNNING pid=18880 hb_age_s=3 stage=resid:L10 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 07:16:16 RUNNING pid=18880 hb_age_s=19 stage=resid:L23 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 07:18:16 RUNNING pid=18880 hb_age_s=13 stage=resid:L32 :: [06:02:26] layer 25: imgΔ=5340.62 txtΔ=92.26 | [06:02:26] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json
- 2026-08-01 07:20:16 RUNNING pid=18880 hb_age_s=61 stage=resid:cache_all :: [07:19:15] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:19:15] PHASE_H_STEP1_CONTAGION
- 2026-08-01 07:22:16 RUNNING pid=18880 hb_age_s=181 stage=resid:cache_all :: [07:19:15] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:19:15] PHASE_H_STEP1_CONTAGION
- 2026-08-01 07:24:16 RUNNING pid=18880 hb_age_s=301 stage=resid:cache_all :: [07:19:15] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:19:15] PHASE_H_STEP1_CONTAGION
- 2026-08-01 07:26:17 RUNNING pid=18880 hb_age_s=422 stage=resid:cache_all :: [07:19:15] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:19:15] PHASE_H_STEP1_CONTAGION
- 2026-08-01 07:28:17 RUNNING pid=18880 hb_age_s=542 stage=resid:cache_all :: [07:19:15] saved C:\Users\arnav\Projects\algoverse\docs\e2e_results.json | [07:19:15] PHASE_H_STEP1_CONTAGION
- 2026-08-01 07:30:17 E2E_COMPLETE detected - guardian idle
- 2026-08-01 07:30:17 guardian_exit
