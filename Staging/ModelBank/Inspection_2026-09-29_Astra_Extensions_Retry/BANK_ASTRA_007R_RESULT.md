# BANK-ASTRA-007R result

[measured: BANK_ASTRA_007R_RECEIPT.json] Three exact ObjectTools.get_properties calls succeeded; zero fallback calls. H0907, H0013 and H0051 each returned PositiveBoundsExtension={"x":0,"y":0,"z":0} and NegativeBoundsExtension={"x":0,"y":0,"z":0}. The sole supported state is bounds_extensions_zero_at_current_revision. Raw requests and replies are preserved in 001_H0907.json, 002_H0013.json and 003_H0051.json. Per-mesh package hashes and prior BANK-ASTRA-004 AABBs appear in the receipt.

[measured: PREFLIGHT.json; LAUNCH.json; SESSION_EDITOR.log; 01_all_saved.jpg; 02_after_reads_all_saved.jpg] Sole editor PID 17272 launched Template_Default at 14:29:14+03:00. Asset discovery completed. All Saved observed before and after reads. Closed with Alt+F4; no dirty prompt or save operation. QUIT_EDITOR at 14:31:07, normal final exit at 14:31:10. Zero relevant processes measured after exit.

[measured: FINAL_VALIDATION_CORRECTED.json] Content 5991 -> 5991: zero added, removed or changed metadata records. All 174 protected hashes identical, including frozen v6 CSV and measurement owner. Saved 85 -> 86: 4 added, 3 removed, 7 changed; Intermediate 11 -> 11: 1 added, 1 removed, 6 changed. Exact deltas are retained separately. Saved deltas concern launch CrashReportClient configuration, log rotation, package restore metadata, auto screenshot, editor user settings, AutoSDK logs and WorldGrid shader debug metadata. Intermediate deltas concern asset-registry cache rotation and Python startup metadata. The asset-registry cache write and orphan-cache deletion are explicitly logged at SESSION_EDITOR.log:2352-2355.

Validation correction: FINAL_VALIDATION.json contains false metadata differences because PowerShell converted JSON timestamps into DateTime objects before comparing them with strings. It is retained for transparency and is superseded by FINAL_VALIDATION_CORRECTED.json, which compares exact string values from both JSON snapshots. Protected hash comparison was unaffected.

ContactValid, FootprintValid, semantic forward and role suitability remain UNKNOWN for all three meshes. ContactXYZ means signed local pivot-to-declared-support point; extension settings are receipt metadata only. No AABB-to-support/footprint inference, no qualification, no flag or candidate CSV edits. No HDA, Houdini, cook, bake, CAT1, INST1, BG1, Tier1 or Linear action.

The bank owner ledger is unchanged. Manager must independently audit and release the editor lease.
