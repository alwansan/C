# Cinemana × Nuvio — Integration workspace (WIP)

**Status: NOT MERGED. No unified APK is available yet.** This is a guarded development branch, not a production release.

## Base versions

- Cinemana: PATCH215 local source workspace (PATCH205 native app/runtime plus later bridge work).
- Nuvio: [NuvioMedia/NuvioMobile at the 0.5.8-beta tag](https://github.com/NuvioMedia/NuvioMobile/tree/0.5.8-beta), commit `1ae5066a4dd5026228625e40082eacc3ada68436`.
- Intended final applicationId: `com.shabakaty.cinemana`. Preserve `CinemanaApplication`, player, native downloader, MKV/subtitles, and Stremio providers.

## CI being exercised

`.github/workflows/nuvio-baseline.yml` compiles the **upstream Nuvio Android UI component only**. Its debug APK must NEVER be labeled a complete Cinemana/Nuvio integration. CI checks the package identity and stores any successful binary under `nuvio-058-fullDebug-component-only` for inspection. Build is fixed to Android SDK 37.0, exposed to Android Gradle Plugin as API 37.

`integration/verify_unified_apk.py` enforces a stricter final release gate: one `com.shabakaty.cinemana` APK with defined DEX classes from **both** Cinemana native runtime/player and Nuvio Compose entry point. This static gate is necessary, but **not sufficient**: video playback, queue/downloads, subtitles, add-ons, account behavior, and Android cold start still require device testing.

## Non-negotiable merge tasks

1. Place PATCH215 source into a trusted build workspace, preserving the exact Smali/native classes and `AndroidManifest.xml`. The conversation ZIP is **not** present in this GitHub repository.
2. Preserve Cinemana resource ID mappings. Assign Nuvio resource IDs in the same linked resource table, **not** by combining two finished APKs or copying their DEX files.
3. Resolve duplicate classes, FileProvider authorities, application startup, launch intents, native libraries, permissions, themes and collision-prone resources.
4. Build Nuvio Compose with its integration changes against a merged manifest and linked Android resource set; keep Cinemana's application runtime.
5. Verify the single APK with `integration/verify_unified_apk.py`, then test on Android before signing a user-facing release.

## Security and distribution

- Repo `alwansan/C` is **public**. Do not commit private signing keys, `local.properties`, tokens, user downloads, or proprietary decompiled source without an explicit distribution decision.
- This branch never embeds signing keys; any successfully built debug APK carries a temporary debug certificate and is **not an in-place update** to the signed Cinemana app.
- Nuvio is GPL-3.0 licensed. Respect its distribution/source requirements.
