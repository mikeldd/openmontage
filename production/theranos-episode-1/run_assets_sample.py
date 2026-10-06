#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.checkpoint import init_project, write_checkpoint
from tools.audio.piper_tts import PiperTTS
from tools.video.stock_sources.base import SearchFilters
from tools.video.stock_sources.coverr import CoverrSource

PROJECT_ID = "healthcare-autopsy-theranos-e01"
PACKAGE_PATH = ROOT / "production" / "theranos-episode-1" / "approved_package.json"

def dump(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piper-dir", required=True)
    args = ap.parse_args()

    pkg = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
    project = init_project(PROJECT_ID, title=pkg["title"], pipeline_type="hybrid")
    artifacts_dir = project / "artifacts"
    dump(artifacts_dir / "brief.json", pkg["brief"])
    dump(artifacts_dir / "script.json", pkg["script"])
    dump(artifacts_dir / "scene_plan.json", pkg["scene_plan"])

    write_checkpoint(ROOT / "projects", PROJECT_ID, "idea", "completed",
        {"brief": pkg["brief"]}, pipeline_type="hybrid", human_approval_required=True, human_approved=True)
    write_checkpoint(ROOT / "projects", PROJECT_ID, "script", "completed",
        {"script": pkg["script"]}, pipeline_type="hybrid", human_approval_required=True, human_approved=True)
    write_checkpoint(ROOT / "projects", PROJECT_ID, "scene_plan", "completed",
        {"scene_plan": pkg["scene_plan"]}, pipeline_type="hybrid", human_approval_required=True, human_approved=True)

    # ---- Required TTS approval sample ----
    sample_text = pkg["script"]["sections"][0]["text"]
    piper_dir = Path(args.piper_dir)
    models = list(piper_dir.glob("en_US-lessac-medium.onnx"))
    if not models:
        raise RuntimeError(f"Piper voice model not found in {piper_dir}")
    narration_path = project / "assets" / "audio" / "sample_hook_piper.wav"
    tts_result = PiperTTS().execute({
        "text": sample_text,
        "model": str(models[0]),
        "speaker_id": 0,
        "length_scale": 1.03,
        "sentence_silence": 0.28,
        "output_path": str(narration_path),
    })
    if not tts_result.success:
        raise RuntimeError(tts_result.error)

    # ---- Required representative visual sample ----
    source = CoverrSource()
    filters = SearchFilters(kind="video", per_page=8, min_duration=5, orientation="landscape", min_width=1280)
    candidate = None
    used_query = None
    for query in ["clinical laboratory", "medical laboratory", "laboratory analyzer"]:
        hits = source.search(query, filters)
        if hits:
            candidate, used_query = hits[0], query
            break
    if candidate is None:
        raise RuntimeError("Coverr returned no suitable laboratory video sample.")

    raw_path = project / "assets" / "video" / "sample_lab_broll_raw.mp4"
    source.download(candidate, raw_path)
    sample_video = project / "assets" / "video" / "sample_lab_broll.mp4"
    subprocess.run([
        "ffmpeg","-y","-i",str(raw_path),"-t","8",
        "-vf","scale=-2:720","-c:v","libx264","-preset","veryfast","-crf","24","-an",str(sample_video)
    ], check=True)
    raw_path.unlink(missing_ok=True)

    source_record = {
        "provider": "coverr",
        "query": used_query,
        "source_id": candidate.source_id,
        "source_url": candidate.source_url,
        "download_url": candidate.download_url,
        "creator": candidate.creator,
        "license": candidate.license,
        "source_tags": candidate.source_tags,
        "duration": candidate.duration,
        "width": candidate.width,
        "height": candidate.height,
    }
    dump(artifacts_dir / "sample_stock_source.json", source_record)

    manifest = {
        "version": "1.0",
        "assets": [
            {
                "id": "sample-narration-hook",
                "type": "narration",
                "path": "assets/audio/sample_hook_piper.wav",
                "source_tool": "piper_tts",
                "scene_id": "s01",
                "model": "en_US-lessac-medium",
                "cost_usd": 0,
                "format": "wav",
                "subtype": "approval_sample",
                "generation_summary": "OpenMontage Piper TTS approval sample for the approved hook only.",
                "provider": "piper",
                "voice_performance": {
                    "source_section_id": "hook",
                    "delivery_cues_applied": True,
                    "provider_text_used": True,
                    "provider_settings": {"length_scale":1.03,"sentence_silence":0.28},
                    "sample_approved": False,
                    "sample_path": "assets/audio/sample_hook_piper.wav",
                    "review_notes": "Awaiting human approval before full narration batch."
                }
            },
            {
                "id": "sample-lab-broll",
                "type": "video",
                "path": "assets/video/sample_lab_broll.mp4",
                "source_tool": "coverr_stock_source",
                "scene_id": "s08",
                "cost_usd": 0,
                "duration_seconds": 8,
                "resolution": "1280x720 preview",
                "format": "mp4",
                "subtype": "stock_approval_sample",
                "generation_summary": "Representative real-motion laboratory B-roll sourced through OpenMontage Coverr adapter.",
                "provider": "coverr",
                "license": candidate.license,
                "original_url": candidate.source_url
            }
        ],
        "total_cost_usd": 0,
        "metadata": {
            "stage": "assets",
            "status": "sample_preview_only",
            "batch_generation_started": False,
            "source_vs_generated_map": {
                "sample-narration-hook": "generated locally by Piper TTS",
                "sample-lab-broll": "real stock footage sourced by OpenMontage"
            }
        }
    }
    dump(artifacts_dir / "asset_manifest.json", manifest)

    decisions = {
      "version":"1.0","project_id":PROJECT_ID,"decisions":[
        {
          "decision_id":"d-assets-001","stage":"assets","category":"voice_selection",
          "subject":"Narration TTS provider approval sample",
          "options_considered":[
            {"option_id":"piper","label":"Piper local TTS","score":0.72,"reason":"Zero-cost, local, deterministic OpenMontage provider suitable for a first approval sample."},
            {"option_id":"cloud-premium","label":"Premium cloud TTS","score":0.86,"reason":"Potentially more natural delivery, but would require a configured paid provider and explicit provider/model approval.","rejected_because":"Not used before the required approval sample."}
          ],
          "selected":"piper","reason":"Generate a no-cost OpenMontage-native sample before any paid or batch narration work.",
          "user_visible":true,"user_approved":false,"confidence":0.95
        },
        {
          "decision_id":"d-assets-002","stage":"assets","category":"provider_selection",
          "subject":"Representative laboratory B-roll source",
          "options_considered":[
            {"option_id":"coverr","label":"Coverr stock video","score":0.90,"reason":"Real motion footage, free commercial-use license, no API key required, supported by OpenMontage."},
            {"option_id":"wikimedia","label":"Wikimedia Commons","score":0.76,"reason":"Excellent provenance/public-license options but less consistent modern clinical B-roll."}
          ],
          "selected":"coverr","reason":"Best fit for a modern clinical-laboratory approval sample with clear licensing and zero API cost.",
          "user_visible":true,"user_approved":false,"confidence":0.92
        }
      ]
    }
    dump(artifacts_dir / "decision_log_assets_sample.json", decisions)

    write_checkpoint(ROOT / "projects", PROJECT_ID, "assets", "awaiting_human",
        {"asset_manifest": manifest, "decision_log": decisions},
        pipeline_type="hybrid", human_approval_required=True, human_approved=False,
        cost_snapshot={"total_spent_usd":0.0,"total_reserved_usd":0.0,"budget_remaining_usd":2.0},
        metadata={"gate":"OpenMontage asset sample approval","batch_generation_started":False})

    print(json.dumps({
        "project": str(project),
        "narration_sample": str(narration_path),
        "video_sample": str(sample_video),
        "source": source_record,
        "status": "awaiting_human"
    }, indent=2))

if __name__ == "__main__":
    main()
